from pydantic import BaseModel, Field
from typing import Optional


class VeterinarianRead(BaseModel):
    id: int
    name: str
    phone: str
    specialization: str
    district: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_available: bool
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class VetBookingCreate(BaseModel):
    veterinarian_id: int
    animal_type: str
    symptoms: str = Field(..., min_length=3)
    preferred_date: str


class VetBookingRead(BaseModel):
    id: int
    user_id: int
    veterinarian_id: int
    animal_type: str
    symptoms: str
    preferred_date: str
    status: str
