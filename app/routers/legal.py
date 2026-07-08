from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["legal"])

# Served directly from the backend so there's a real, stable public URL
# the moment the backend is deployed — no separate hosting (GitHub Pages,
# etc.) needed just for this one page. Google Play requires this URL in
# the Play Console listing before it will accept a submission.
#
# Read before publishing: replace CONTACT_EMAIL below with a real,
# monitored email address. "your-email@example.com" will not pass Play
# Console review, and more importantly, someone needs to actually be able
# to reach you about their data.
CONTACT_EMAIL = "your-email@example.com"

PRIVACY_POLICY_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>YerevanServices — Privacy Policy</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #1c1a19; }}
    h1 {{ font-size: 1.6em; }}
    h2 {{ font-size: 1.2em; margin-top: 2em; }}
    footer {{ margin-top: 3em; color: #777; font-size: 0.9em; }}
  </style>
</head>
<body>
  <h1>Privacy Policy — YerevanServices</h1>
  <p>Last updated: 2026. This policy explains what information the YerevanServices
  app ("the app") collects, why, and how you can remove it.</p>

  <h2>Information we collect</h2>
  <ul>
    <li><strong>Email address</strong> — used only to sign you in (we send a one-time
    verification code to it). We do not use it for marketing.</li>
    <li><strong>Display name</strong> — shown publicly on any service listing you post.</li>
    <li><strong>Phone number</strong> — optional, shown publicly on your listings so
    buyers can contact you. Not used for login.</li>
    <li><strong>Approximate location</strong> — attached to listings you post, so
    others can find services near them.</li>
    <li><strong>Listing content</strong> — the title, description, category, and
    price of anything you post.</li>
  </ul>

  <h2>What we don't do</h2>
  <ul>
    <li>We do not sell your data to third parties.</li>
    <li>We do not show ads or share your data with advertisers.</li>
    <li>We do not track you across other apps or websites.</li>
  </ul>

  <h2>Third-party services we use</h2>
  <p>We use an email delivery provider solely to send sign-in verification
  codes. That provider processes your email address only for that purpose
  and does not receive any other data about you.</p>

  <h2>Data retention</h2>
  <p>Your account data and listings are kept until you delete them or delete
  your account. Verification codes are automatically deleted a few minutes
  after being sent, whether used or not.</p>

  <h2>Deleting your data</h2>
  <p>You can permanently delete your account and every listing you've posted
  at any time, directly in the app: <strong>Account → Delete account</strong>.
  This is immediate and cannot be undone.</p>

  <h2>Children's privacy</h2>
  <p>This app is not directed at children under 13, and we do not knowingly
  collect data from children under 13.</p>

  <h2>Contact</h2>
  <p>Questions about this policy or your data can be sent to
  <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>

  <footer>YerevanServices is an independent, student-built project and is not
  affiliated with any government body.</footer>
</body>
</html>
"""


@router.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy():
    return PRIVACY_POLICY_HTML
