from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------

class SendCodeRequest(BaseModel):
    email: EmailStr


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=8)
    # Both optional: only used to set/update the profile the first time
    # this email signs in — an email OTP gives us no name or contact
    # phone on its own, so this is the one moment to collect them
    # without adding an extra screen.
    display_name: Optional[str] = Field(None, max_length=80)
    phone_number: Optional[str] = Field(None, max_length=20)


class UserOut(BaseModel):
    id: str
    email: str
    display_name: str
    phone_number: Optional[str] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Services ----------

class GeoPoint(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class ServiceCreate(BaseModel):
    title: str = Field(..., max_length=80)
    description: str = Field(..., max_length=1000)
    category: str
    price_amd: int = Field(..., gt=0)
    location: GeoPoint
    # Lets the app set/refresh the poster's name and contact phone at
    # post time, same reasoning as VerifyCodeRequest above — useful if
    # they signed up without one and are adding it now.
    owner_name: Optional[str] = Field(None, max_length=80)
    owner_phone: Optional[str] = Field(None, max_length=20)


class ServiceOut(BaseModel):
    id: str
    owner_uid: str
    owner_name: str
    owner_phone: Optional[str] = None
    title: str
    description: str
    category: str
    price_amd: int
    location: GeoPoint
    created_at: Optional[datetime] = None
    distance_km: Optional[float] = None
    is_active: bool = True

    model_config = {"from_attributes": True}


class ServiceStatusUpdate(BaseModel):
    is_active: bool
