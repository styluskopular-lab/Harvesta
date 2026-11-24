from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.app_review import AppReview
from app.models.user import User
from app.schemas.review import AppReviewCreate, AppReviewRead, ReviewPromptStatus

router = APIRouter(prefix="/reviews", tags=["App Reviews"])


def _account_age_days(created_at: datetime) -> int:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    elapsed = datetime.now(timezone.utc) - created_at
    return max(0, elapsed.days)


@router.get("/prompt", response_model=ReviewPromptStatus)
def review_prompt_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = (
        db.query(AppReview)
        .filter(AppReview.user_id == current_user.id)
        .first()
    )
    age_days = _account_age_days(current_user.created_at)
    return ReviewPromptStatus(
        eligible=age_days >= 7 and review is None,
        submitted=review is not None,
        account_age_days=age_days,
        review=review,
    )


@router.post("/", response_model=AppReviewRead, status_code=status.HTTP_201_CREATED)
def submit_review(
    review_in: AppReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(AppReview.id)
        .filter(AppReview.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="A review has already been submitted")

    review = AppReview(
        user_id=current_user.id,
        rating=review_in.rating,
        comments=review_in.comments.strip() or None
        if review_in.comments is not None
        else None,
    )
    db.add(review)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A review has already been submitted",
        ) from exc
    db.refresh(review)
    return review
