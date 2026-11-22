from datetime import datetime, timezone
from sqlalchemy import String, Float, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Veterinarian(Base):
    __tablename__ = "veterinarians"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    specialization: Mapped[str] = mapped_column(String(150), nullable=False)
    district: Mapped[str] = mapped_column(String(150), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    bookings = relationship("VetBooking", back_populates="veterinarian")


class VetBooking(Base):
    __tablename__ = "vet_bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    veterinarian_id: Mapped[int] = mapped_column(ForeignKey("veterinarians.id"), nullable=False)
    animal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    preferred_date: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="requested", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    veterinarian = relationship("Veterinarian", back_populates="bookings")
