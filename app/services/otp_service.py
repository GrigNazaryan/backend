from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, generate_otp, hash_code
from app.models.db_models import OtpCode, User
from app.services.email import get_email_provider

OTP_TTL_MINUTES = 5
RESEND_COOLDOWN_SECONDS = 60
MAX_VERIFY_ATTEMPTS = 5


class OtpError(Exception):
    """Raised for any user-facing OTP failure (wrong code, expired,
    too many attempts, sent too recently). The message is safe to show
    directly in the app."""


def send_verification_code(db: Session, email: str) -> None:
    recent = db.execute(
        select(OtpCode)
        .where(OtpCode.email == email, OtpCode.consumed.is_(False))
        .order_by(OtpCode.created_at.desc())
    ).scalars().first()

    now = datetime.now(timezone.utc)
    if recent and (now - recent.created_at).total_seconds() < RESEND_COOLDOWN_SECONDS:
        wait = RESEND_COOLDOWN_SECONDS - int((now - recent.created_at).total_seconds())
        raise OtpError(f"Please wait {wait}s before requesting another code.")

    code = generate_otp()
    otp_row = OtpCode(
        email=email,
        code_hash=hash_code(code),
        expires_at=now + timedelta(minutes=OTP_TTL_MINUTES),
    )
    db.add(otp_row)
    db.commit()

    get_email_provider().send_email(
        email,
        "Your Yerevan Services verification code",
        f"Your verification code is {code}. It expires in {OTP_TTL_MINUTES} minutes.\n\n"
        "If you didn't request this, you can safely ignore this email.",
    )


def verify_code_and_sign_in(
    db: Session,
    email: str,
    code: str,
    display_name: str | None,
    phone_number: str | None,
) -> tuple[User, str]:
    otp_row = db.execute(
        select(OtpCode)
        .where(OtpCode.email == email, OtpCode.consumed.is_(False))
        .order_by(OtpCode.created_at.desc())
    ).scalars().first()

    if otp_row is None:
        raise OtpError("No code was requested for this email. Request a new one.")

    now = datetime.now(timezone.utc)
    if now > otp_row.expires_at:
        otp_row.consumed = True
        db.commit()
        raise OtpError("This code has expired. Request a new one.")

    if otp_row.attempts >= MAX_VERIFY_ATTEMPTS:
        otp_row.consumed = True
        db.commit()
        raise OtpError("Too many attempts. Request a new code.")

    if otp_row.code_hash != hash_code(code):
        otp_row.attempts += 1
        db.commit()
        raise OtpError("That code isn't right. Double-check and try again.")

    otp_row.consumed = True
    db.commit()

    user = db.execute(select(User).where(User.email == email)).scalars().first()
    if user is None:
        user = User(
            email=email,
            display_name=display_name or "Unnamed user",
            phone_number=phone_number,
        )
        db.add(user)
    else:
        if display_name and user.display_name in ("Unnamed user", ""):
            user.display_name = display_name
        if phone_number and not user.phone_number:
            user.phone_number = phone_number
    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id, email=user.email)
    return user, token
