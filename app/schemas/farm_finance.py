from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class FarmTransactionCreate(BaseModel):
    transaction_type: str = Field(..., pattern="^(income|expense)$")
    category: str = Field(..., min_length=2, max_length=100)
    amount: float = Field(..., gt=0)
    transaction_date: date
    description: Optional[str] = None


class FarmTransactionRead(FarmTransactionCreate):
    id: int
    owner_id: int
    created_at: datetime
    model_config = {"from_attributes": True}
