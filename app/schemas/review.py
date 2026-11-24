from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AppReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comments: Optional[str] = Field(default=None, max_length=2000)


class AppReviewRead(BaseModel):
    id: int
    rating: int
    comments: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewPromptStatus(BaseModel):
    eligible: bool
    submitted: bool
    account_age_days: int
    review: Optional[AppReviewRead] = None
