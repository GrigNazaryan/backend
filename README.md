# Yerevan Services API (v2 — self-hosted)

FastAPI + PostgreSQL backend for the Yerevan Services marketplace. Fully
self-hosted: your own database, your own JWT-based sessions, and a swappable
email provider for sign-in codes. No Firebase, no Twilio, no third-party BaaS
required to run this.

## Architecture

```
app/
  core/
    config.py       — settings from environment variables
    database.py       — SQLAlchemy engine/session (forces UTF-8 client encoding)
    security.py         — JWT creation/verification, OTP hashing
    deps.py               — get_current_user (JWT bearer auth dependency)
  models/
    db_models.py            — SQLAlchemy tables: User, Service, OtpCode
    schemas.py                — Pydantic request/response shapes
  services/
    otp_service.py             — generate/send/verify OTP codes
    services_repository.py      — DB queries for listings (create/search+filter/delete)
    email/
      base.py                     — EmailProvider interface
      console_provider.py           — dev-mode: prints the code instead of sending it
      smtp_provider.py                — real email via any SMTP server
  routers/
    auth.py                           — /auth/send-code, /auth/verify-code, /auth/me, delete account
    services.py                         — /services (create/browse/get/delete)
    legal.py                              — /privacy-policy (served as HTML, see below)
  main.py                                  — app assembly, creates tables on startup
```

## Data model

- **User**: `id` (UUID), `email` (unique, used for login), `display_name`,
  `phone_number` (optional — contact number shown on listings, unrelated to login), `created_at`
- **Service**: `id` (UUID), `owner_id` (FK, cascades on account deletion),
  denormalized `owner_name`/`owner_phone` (snapshot at post time), `title`,
  `description`, `category`, `price_amd`, `lat`/`lng`, `created_at`
- **OtpCode**: short-lived verification codes — `email`, `code_hash` (never
  the raw code), `expires_at`, `attempts`, `consumed`

## Auth flow — email, not SMS

1. `POST /auth/send-code` `{"email": "grig@example.com"}` — generates a
   6-digit code, stores its hash, emails it via the configured provider.
   Rate-limited to one send per 60 seconds per address.
2. `POST /auth/verify-code`
   `{"email": "...", "code": "123456", "display_name": "Grig", "phone_number": "+37455123456"}`
   — validates the code (max 5 attempts, 5-minute expiry), creates the user on
   first sign-in, returns a JWT:
   ```json
   { "access_token": "...", "token_type": "bearer",
     "user": {"id": "...", "email": "...", "display_name": "...", "phone_number": "..."} }
   ```
   `display_name`/`phone_number` are optional and only take effect the first
   time — an email OTP carries no name or phone on its own, so the app
   collects them once at sign-up.
3. The app sends `Authorization: Bearer <access_token>` on every write
   (`POST/DELETE /services`, `DELETE /auth/me`).
4. Tokens last `JWT_EXPIRES_DAYS` (default 30) — no refresh-token flow. When a
   token expires, the app just asks the user to sign in again.

**Why email instead of phone/SMS**: no per-message cost, no carrier region
restrictions, no billing account needed to get started — `EMAIL_PROVIDER=console`
works immediately with zero setup for development.

## Account deletion (Google Play requirement)

`DELETE /auth/me` (authenticated) permanently deletes the signed-in user and
every listing they've posted — not just a sign-out. Google Play requires
apps with user accounts to offer in-app deletion, not merely a sign-out
button; this satisfies that. The `Service.owner_id` foreign key cascades at
both the ORM and database level, so deletion is complete even if something
ever deletes a user via raw SQL.

## Privacy Policy (Google Play requirement)

Served directly by this backend at `GET /privacy-policy` — once deployed,
that's a real, stable public URL (e.g. `https://your-app.onrender.com/privacy-policy`)
with zero extra hosting setup. **Before submitting to Play Console**, open
`app/routers/legal.py` and replace `CONTACT_EMAIL` with a real, monitored
address — the placeholder will not pass review.

## Data Safety form (Google Play requirement)

Play Console has a separate questionnaire ("Data safety") about what your app
collects — this isn't something code can fill in for you, but here's exactly
what to answer, matching what this backend actually does:

| Data type | Collected? | Shared with 3rd parties? | Purpose |
|---|---|---|---|
| Email address | Yes | No | Account creation / sign-in |
| Name | Yes | No | Shown on listings the user posts |
| Phone number | Yes (optional) | No | Shown on listings so buyers can call |
| Approximate location | Yes | No | Attached to listings for "nearby" search |
| User-generated content | Yes (listing text/price) | No | Core app functionality |

Also answer:
- **Is data encrypted in transit?** Yes (HTTPS, once deployed with a real
  domain — see Deployment below).
- **Can users request data deletion?** Yes — in-app, immediate (see above).
- **Is data collection required or optional?** Email is required to post a
  listing; browsing requires no account at all.

## Search + filter (combined)

`GET /services?category=tutoring&search=math` returns only listings matching
**both** — category and search text are ANDed, not ORed. Clearing one leaves
the other applied.

## Local development

```bash
docker compose up --build
```
Starts Postgres + the API together.
- API: http://127.0.0.1:8000/docs
- OTP codes print to the `backend` container's logs (`EMAIL_PROVIDER=console` by default) — no real email sent, zero cost, while you develop.

Without Docker:
```bash
python3 -m venv venv
venv\Scripts\activate        # Windows; use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env         # edit DATABASE_URL, JWT_SECRET
uvicorn app.main:app --reload --host 0.0.0.0
```

## Email integration — enabling real emails

Behind `app/services/email/base.py`'s `EmailProvider` interface — the rest of
the app only calls `get_email_provider().send_email(...)`.

| Provider | `EMAIL_PROVIDER=` | Use for |
|---|---|---|
| Console | `console` (default) | Local dev — logs the code, zero cost |
| SMTP    | `smtp`               | Real email via Gmail, Outlook, or any SMTP server |

### Enabling real email via Gmail

1. Use a Gmail account (a dedicated one for the app is cleaner than a personal one).
2. Turn on 2-Step Verification on that account (required for the next step).
3. Create an **App Password**: Google Account → Security → 2-Step Verification →
   App passwords → generate one for "Mail".
4. Set in `.env`:
   ```
   EMAIL_PROVIDER=smtp
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-app-gmail@gmail.com
   SMTP_PASSWORD=<the 16-character app password, not your real Gmail password>
   SMTP_FROM_ADDRESS=your-app-gmail@gmail.com
   ```
5. Restart the backend. `/auth/send-code` now sends real email.

Any other SMTP provider (Outlook, Yandex, a custom domain, or SendGrid/Mailgun's
SMTP relay) works the same way — just change `SMTP_HOST`/`SMTP_PORT` and use
that provider's credentials.

## Deployment — quick path (Render)

Your current `apiBaseUrl` in the Flutter app already points at
`https://backend-xk4a.onrender.com` — if that's this backend already deployed,
you can skip to updating environment variables in the Render dashboard.
Otherwise, from scratch:

1. Push this `backend/` folder to a GitHub repo.
2. [render.com](https://render.com) → **New → Web Service** → connect the repo → it detects the `Dockerfile`.
3. **New → PostgreSQL** (separate service) → copy its "Internal Database URL".
4. On the web service, set environment variables:
   ```
   DATABASE_URL=<the internal database URL from step 3>
   JWT_SECRET=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
   JWT_EXPIRES_DAYS=30
   CORS_ORIGINS=*
   EMAIL_PROVIDER=smtp
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-app-gmail@gmail.com
   SMTP_PASSWORD=your-app-password
   SMTP_FROM_ADDRESS=your-app-gmail@gmail.com
   ```
5. Deploy. You'll get a public HTTPS URL — that's also your Privacy Policy URL
   with `/privacy-policy` appended, ready to paste into Play Console.

Railway works almost identically and auto-links its Postgres plugin's
`DATABASE_URL` for you, if you'd rather use that instead.

## Known simplifications (fine for an MVP, worth revisiting later)

- No Alembic migrations — schema changes beyond adding new tables will need
  manual `ALTER TABLE` or introducing Alembic at that point.
- No refresh tokens — a 30-day JWT is simple but means a stolen token stays
  valid for its full lifetime.
- Distance search fetches matching rows into Python and filters with `geopy`
  rather than a PostGIS geospatial query — fine at hundreds/low-thousands of
  listings, would need revisiting at real scale.
