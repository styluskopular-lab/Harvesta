from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.models.farm import Farm
from app.schemas.farm import FarmCreate, FarmRead, FarmUpdate

router = APIRouter(prefix="/farms", tags=["Farms"])


@router.post("/", response_model=FarmRead, status_code=status.HTTP_201_CREATED)
def create_farm(
    farm_in: FarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("farmer", "admin")),
):
    farm = Farm(**farm_in.model_dump(), owner_id=current_user.id)
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/me", response_model=List[FarmRead])
def my_farms(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("farmer", "admin")),
):
    return db.query(Farm).filter(Farm.owner_id == current_user.id).all()


@router.get("/{farm_id}", response_model=FarmRead)
def get_farm(farm_id: int, db: Session = Depends(get_db)):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.put("/{farm_id}", response_model=FarmRead)
def update_farm(
    farm_id: int,
    farm_in: FarmUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("farmer", "admin")),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if farm.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    for field, value in farm_in.model_dump(exclude_unset=True).items():
        setattr(farm, field, value)
    db.commit()
    db.refresh(farm)
    return farm
