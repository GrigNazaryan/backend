import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80), default="Unnamed user")
    # Contact phone shown on listings so buyers can call — separate from
    # auth entirely now. Nullable: a user can sign in and browse without
    # ever setting one, but posting a listing should collect it.
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    services: Mapped[list["Service"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # Denormalized snapshot of the owner's name/phone at post time. This
    # avoids a join on every listings read (the common case, browsing),
    # at the cost of listings not retroactively updating if someone
    # changes their name later — an acceptable tradeoff for a
    # marketplace where a listing is a point-in-time offer anyway.
    owner_name: Mapped[str] = mapped_column(String(80))
    owner_phone: Mapped[str] = mapped_column(String(20))

    title: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(40), index=True)
    price_amd: Mapped[int] = mapped_column(Integer)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    # Lets an owner pause a listing (hide it from public browsing) without
    # deleting it outright — the "Active" vs "My listings" split in the app.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    # Lets an owner pause a listing (hide it from public browse) without
    # deleting it outright — distinct from delete, which is permanent.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    owner: Mapped["User"] = relationship(back_populates="services")


class OtpCode(Base):
    """A one-time email verification code. Rows are short-lived — created
    on /auth/send-code, consumed (or expired) shortly after."""

    __tablename__ = "otp_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
