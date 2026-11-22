from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.veterinary import Veterinarian, VetBooking
from app.schemas.veterinary import VeterinarianRead, VetBookingCreate, VetBookingRead

router = APIRouter(prefix="/veterinary", tags=["Veterinary"])


@router.get("/providers", response_model=list[VeterinarianRead])
def list_providers(district: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Veterinarian).filter(Veterinarian.is_available == True)
    if district:
        query = query.filter(Veterinarian.district.ilike(f"%{district}%"))
    return query.all()


@router.post("/bookings", response_model=VetBookingRead, status_code=201)
def create_booking(
    booking_in: VetBookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    provider = db.query(Veterinarian).filter(Veterinarian.id == booking_in.veterinarian_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Veterinary provider not found")
    booking = VetBooking(
        user_id=current_user.id,
        veterinarian_id=provider.id,
        animal_type=booking_in.animal_type,
        symptoms=booking_in.symptoms,
        preferred_date=booking_in.preferred_date,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("/bookings", response_model=list[VetBookingRead])
def list_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(VetBooking).filter(VetBooking.user_id == current_user.id).all()
