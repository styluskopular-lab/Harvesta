from datetime import date, datetime, timezone
from sqlalchemy import String, Integer, Float, Text, ForeignKey, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CropPlot(Base):
    __tablename__ = "crop_plots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    plot_name: Mapped[str] = mapped_column(String(150), nullable=False)
    crop_type: Mapped[str] = mapped_column(String(100), nullable=False)
    variety: Mapped[str | None] = mapped_column(String(150), nullable=True)
    planting_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_harvest_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    crop_stage: Mapped[str] = mapped_column(String(100), default="Land Preparation", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class LivestockAnimal(Base):
    __tablename__ = "livestock_animals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    animal_name: Mapped[str] = mapped_column(String(150), nullable=False)
    animal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    breed: Mapped[str] = mapped_column(String(100), nullable=False)
    tag_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sex: Mapped[str] = mapped_column(String(20), default="Female", nullable=False)
    service_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Registered", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
