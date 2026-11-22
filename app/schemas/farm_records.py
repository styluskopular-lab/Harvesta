from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class CropPlotCreate(BaseModel):
    plot_name: str = Field(..., min_length=2, max_length=150)
    crop_type: str = Field(..., min_length=2, max_length=100)
    variety: Optional[str] = None
    planting_date: date
    expected_harvest_date: Optional[date] = None
    expected_harvest_days: Optional[int] = Field(default=None, ge=1, le=3650)
    crop_stage: str = "Land Preparation"
    notes: Optional[str] = None


class CropPlotRead(CropPlotCreate):
    id: int
    owner_id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class LivestockAnimalCreate(BaseModel):
    animal_name: str = Field(..., min_length=1, max_length=150)
    animal_type: str = Field(..., min_length=2, max_length=50)
    breed: str = Field(..., min_length=2, max_length=100)
    tag_number: Optional[str] = None
    sex: str = "Female"
    service_date: Optional[date] = None


class LivestockAnimalRead(LivestockAnimalCreate):
    id: int
    owner_id: int
    due_date: Optional[date]
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
