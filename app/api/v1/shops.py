from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.models.shop import Shop, ShopInventory
from app.schemas.shop import ShopCreate, ShopRead, ShopInventoryCreate, ShopInventoryRead

router = APIRouter(prefix="/shops", tags=["Shops"])


@router.post("/", response_model=ShopRead, status_code=status.HTTP_201_CREATED)
def create_shop(
    shop_in: ShopCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    shop = Shop(**shop_in.model_dump())
    db.add(shop)
    db.commit()
    db.refresh(shop)
    return shop


@router.get("/", response_model=List[ShopRead])
def list_shops(db: Session = Depends(get_db)):
    return db.query(Shop).all()


@router.get("/{shop_id}", response_model=ShopRead)
def get_shop(shop_id: int, db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


@router.post("/inventory", response_model=ShopInventoryRead, status_code=status.HTTP_201_CREATED)
def add_inventory(
    inv_in: ShopInventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "shop_manager")),
):
    inv = ShopInventory(**inv_in.model_dump())
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.get("/{shop_id}/inventory", response_model=List[ShopInventoryRead])
def get_shop_inventory(shop_id: int, db: Session = Depends(get_db)):
    return db.query(ShopInventory).filter(ShopInventory.shop_id == shop_id).all()
