import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


def hash_code(code: str) -> str:
    """Plain SHA-256 is fine here (not bcrypt/argon2): OTP codes are
    6 digits, short-lived (minutes), and rate-limited on attempts — this
    isn't protecting a long-lived password, just avoiding storing the
    raw code in the database."""
    return hashlib.sha256(code.encode()).hexdigest()


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expires_days)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError (caught by the caller) on any invalid/expired token."""
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
