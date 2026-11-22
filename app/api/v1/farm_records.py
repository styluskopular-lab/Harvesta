from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.farm_records import CropPlot, LivestockAnimal
from app.schemas.farm_records import (
    CropPlotCreate, CropPlotRead,
    LivestockAnimalCreate, LivestockAnimalRead,
)

router = APIRouter(prefix="/farm-records", tags=["Farm Records"])


@router.post("/crop-plots", response_model=CropPlotRead, status_code=201)
def create_crop_plot(
    payload: CropPlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {"farmer", "admin"}:
        raise HTTPException(status_code=403, detail="Only farmers can manage crop plots")
    data = payload.model_dump()
    if data.get("expected_harvest_days"):
        data["expected_harvest_date"] = payload.planting_date + timedelta(days=data["expected_harvest_days"])
    if not data.get("expected_harvest_date"):
        maturity_days = {
            "maize": 120,
            "matooke": 270,
            "beans": 90,
            "irish potatoes": 120,
            "cassava": 300,
            "coffee robusta": 1095,
            "coffee arabica": 1095,
            "rice": 120,
            "cabbage": 90,
            "tomatoes": 120,
        }
        days = maturity_days.get(payload.crop_type.strip().lower(), 120)
        data["expected_harvest_date"] = payload.planting_date + timedelta(days=days)
    plot = CropPlot(owner_id=current_user.id, **data)
    db.add(plot)
    db.commit()
    db.refresh(plot)
    return plot


@router.get("/crop-plots", response_model=list[CropPlotRead])
def list_crop_plots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(CropPlot).filter(CropPlot.owner_id == current_user.id).order_by(CropPlot.planting_date.desc()).all()


@router.delete("/crop-plots/{plot_id}", status_code=204)
def delete_crop_plot(
    plot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plot = db.query(CropPlot).filter(CropPlot.id == plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Crop plot not found")
    if plot.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(plot)
    db.commit()
    return None


GESTATION_DAYS = {"cattle": 283, "goat": 150, "goats": 150, "pig": 114, "pigs": 114}


@router.post("/livestock", response_model=LivestockAnimalRead, status_code=201)
def register_livestock(
    payload: LivestockAnimalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {"farmer", "admin"}:
        raise HTTPException(status_code=403, detail="Only farmers can manage livestock")
    data = payload.model_dump()
    animal_type = payload.animal_type.strip().lower()
    due_date = None
    status_value = "Registered"
    if payload.service_date:
        days = GESTATION_DAYS.get(animal_type)
        if days:
            due_date = payload.service_date + timedelta(days=days)
            today = date.today()
            if due_date < today:
                status_value = "OVERDUE"
            elif due_date - today <= timedelta(days=14):
                status_value = "DUE SOON — 14 DAYS OUT"
            else:
                status_value = "ON TRACK"
    animal = LivestockAnimal(
        owner_id=current_user.id,
        due_date=due_date,
        status=status_value,
        **data,
    )
    db.add(animal)
    db.commit()
    db.refresh(animal)
    return animal


@router.get("/livestock", response_model=list[LivestockAnimalRead])
def list_livestock(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    animals = db.query(LivestockAnimal).filter(LivestockAnimal.owner_id == current_user.id).order_by(LivestockAnimal.created_at.desc()).all()
    today = date.today()
    for animal in animals:
        if animal.due_date:
            if animal.due_date < today:
                animal.status = "OVERDUE"
            elif animal.due_date - today <= timedelta(days=14):
                animal.status = "DUE SOON — 14 DAYS OUT"
            else:
                animal.status = "ON TRACK"
    db.commit()
    return animals


@router.delete("/livestock/{animal_id}", status_code=204)
def delete_livestock(
    animal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    animal = db.query(LivestockAnimal).filter(LivestockAnimal.id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Livestock record not found")
    if animal.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(animal)
    db.commit()
    return None
