from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FarmBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    location: str
    size_hectares: Optional[float] = None
    crop_types: Optional[str] = None
    livestock: Optional[str] = None
    description: Optional[str] = None


class FarmCreate(FarmBase):
    pass


class FarmUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    size_hectares: Optional[float] = None
    crop_types: Optional[str] = None
    livestock: Optional[str] = None
    description: Optional[str] = None


class FarmRead(FarmBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
