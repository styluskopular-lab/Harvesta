from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)
    phone: Optional[str] = None
    role: str = "buyer"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    notification_preference: Literal["email", "sms", "both"] = "email"
    privacy_consent: bool = False
    privacy_consent_at: Optional[datetime] = None
    nin: Optional[str] = None
    date_of_birth: Optional[date] = None
    district: Optional[str] = None
    subcounty: Optional[str] = None
    village: Optional[str] = None
    next_of_kin_name: Optional[str] = None
    next_of_kin_contact: Optional[str] = None
    primary_farm_enterprise: Optional[str] = None
    farm_size_acres: Optional[float] = None
    dfa_cooperative_id: Optional[str] = None
    driving_permit_number: Optional[str] = None
    driving_permit_class: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    goods_insurance_status: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    privacy_consent: bool = Field(..., description="User consent to privacy policy")
    nin: str = Field(..., min_length=14, max_length=14)
    date_of_birth: date
    district: str = Field(..., min_length=2)
    subcounty: Optional[str] = Field(default=None)
    village: str = Field(..., min_length=2)
    next_of_kin_name: str = Field(..., min_length=2)
    next_of_kin_contact: str = Field(..., min_length=6)
    primary_farm_enterprise: Optional[str] = None
    farm_size_acres: Optional[float] = Field(default=None, ge=0)
    dfa_cooperative_id: Optional[str] = None
    driving_permit_number: Optional[str] = None
    driving_permit_class: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    goods_insurance_status: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    notification_preference: Optional[Literal["email", "sms", "both"]] = None


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterResponse(UserRead):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str
