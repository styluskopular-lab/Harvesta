from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    get_current_user,
)
from app.core.config import settings
from app.models.user import User
from app.models.farm import Farm
from app.models.product import Product
from app.models.order import Order
from app.models.farm_records import CropPlot, LivestockAnimal
from app.models.farm_finance import FarmTransaction
from app.models.wallet import WalletTransaction
from app.models.app_review import AppReview
from app.models.notification import NotificationLog
from app.services.wallet import wallet_balance_ugx
from app.schemas.user import (
    LoginRequest,
    RegisterResponse,
    Token,
    UserCreate,
    UserRead,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
@router.post("/register/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if not user_in.privacy_consent:
        raise HTTPException(status_code=400, detail="Privacy Policy and Terms of Use consent is required")
    nin = user_in.nin.strip().upper()
    if not (nin[:2] in {"CM", "CF"} and len(nin) == 14 and nin.isalnum()):
        raise HTTPException(status_code=400, detail="NIN must be a 14-character NIRA format beginning with CM or CF")
    today = datetime.now(timezone.utc).date()
    age = today.year - user_in.date_of_birth.year - (
        (today.month, today.day) < (user_in.date_of_birth.month, user_in.date_of_birth.day)
    )
    if age < 18:
        raise HTTPException(status_code=400, detail="You must be at least 18 years old")
    existing_nin = db.query(User).filter(User.nin == nin).first()
    if existing_nin:
        raise HTTPException(status_code=400, detail="NIN already registered")
    if user_in.role == "farmer" and not user_in.primary_farm_enterprise:
        raise HTTPException(status_code=400, detail="Primary farm enterprise is required for farmers")
    if user_in.role == "driver":
        required_driver_fields = [
            user_in.driving_permit_number,
            user_in.driving_permit_class,
            user_in.vehicle_type,
            user_in.vehicle_plate,
            user_in.goods_insurance_status,
        ]
        if any(not value for value in required_driver_fields):
            raise HTTPException(status_code=400, detail="Complete permit, vehicle, plate and insurance details are required for drivers")
    normalized_email = str(user_in.email).strip().lower()
    if not normalized_email.endswith("@gmail.com"):
        raise HTTPException(status_code=400, detail="Please use a Gmail address")

    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    if user_in.phone:
        existing_phone = db.query(User).filter(User.phone == user_in.phone.strip()).first()
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone number already registered")
    if user_in.role not in {"buyer", "farmer", "driver", "shop_manager"}:
        raise HTTPException(status_code=400, detail="Invalid account role")

    user = User(
        email=normalized_email,
        full_name=user_in.full_name,
        phone=user_in.phone,
        role=user_in.role,
        notification_preference=user_in.notification_preference,
        latitude=user_in.latitude,
        longitude=user_in.longitude,
        location_name=user_in.location_name,
        nin=nin,
        date_of_birth=user_in.date_of_birth,
        district=user_in.district,
        subcounty=user_in.subcounty,
        village=user_in.village,
        next_of_kin_name=user_in.next_of_kin_name,
        next_of_kin_contact=user_in.next_of_kin_contact,
        primary_farm_enterprise=user_in.primary_farm_enterprise,
        farm_size_acres=user_in.farm_size_acres,
        dfa_cooperative_id=user_in.dfa_cooperative_id,
        driving_permit_number=user_in.driving_permit_number,
        driving_permit_class=user_in.driving_permit_class,
        vehicle_type=user_in.vehicle_type,
        vehicle_plate=user_in.vehicle_plate,
        goods_insurance_status=user_in.goods_insurance_status,
        privacy_consent=user_in.privacy_consent,
        privacy_consent_at=datetime.now(timezone.utc) if user_in.privacy_consent else None,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role,
        "notification_preference": user.notification_preference,
        "latitude": user.latitude,
        "longitude": user.longitude,
        "location_name": user.location_name,
        "nin": user.nin,
        "date_of_birth": user.date_of_birth,
        "district": user.district,
        "subcounty": user.subcounty,
        "village": user.village,
        "next_of_kin_name": user.next_of_kin_name,
        "next_of_kin_contact": user.next_of_kin_contact,
        "primary_farm_enterprise": user.primary_farm_enterprise,
        "farm_size_acres": user.farm_size_acres,
        "dfa_cooperative_id": user.dfa_cooperative_id,
        "driving_permit_number": user.driving_permit_number,
        "driving_permit_class": user.driving_permit_class,
        "vehicle_type": user.vehicle_type,
        "vehicle_plate": user.vehicle_plate,
        "goods_insurance_status": user.goods_insurance_status,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
@router.post("/login/", response_model=Token, include_in_schema=False)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm uses "username" field for email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login/json", response_model=Token)
@router.post("/login/json/", response_model=Token, include_in_schema=False)
def login_json(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Alternative login endpoint that accepts JSON body (useful for Streamlit)."""
    identifier = login_data.email.strip()
    user = db.query(User).filter(
        (User.email == identifier) | (User.phone == identifier)
    ).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserRead)
def update_users_me(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    update_data = user_in.model_dump(exclude_unset=True, exclude={"is_active"})
    if "notification_preference" in update_data and not update_data["notification_preference"]:
        raise HTTPException(status_code=422, detail="Choose a notification preference")
    for field, value in update_data.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/export")
def export_my_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {
        "account": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "phone": current_user.phone,
            "role": current_user.role,
            "notification_preference": current_user.notification_preference,
            "location_name": current_user.location_name,
            "nin": current_user.nin,
            "date_of_birth": current_user.date_of_birth,
            "district": current_user.district,
            "subcounty": current_user.subcounty,
            "village": current_user.village,
            "next_of_kin_name": current_user.next_of_kin_name,
            "next_of_kin_contact": current_user.next_of_kin_contact,
            "primary_farm_enterprise": current_user.primary_farm_enterprise,
            "farm_size_acres": current_user.farm_size_acres,
            "dfa_cooperative_id": current_user.dfa_cooperative_id,
            "driving_permit_number": current_user.driving_permit_number,
            "driving_permit_class": current_user.driving_permit_class,
            "vehicle_type": current_user.vehicle_type,
            "vehicle_plate": current_user.vehicle_plate,
            "goods_insurance_status": current_user.goods_insurance_status,
            "privacy_consent": current_user.privacy_consent,
            "privacy_consent_at": current_user.privacy_consent_at,
        },
        "farms": [
            {"id": item.id, "name": item.name, "location": item.location,
             "size_hectares": item.size_hectares, "crop_types": item.crop_types,
             "livestock": item.livestock, "description": item.description}
            for item in db.query(Farm).filter(Farm.owner_id == current_user.id).all()
        ],
        "products": [
            {"id": item.id, "name": item.name, "category": item.category,
             "quantity": item.quantity, "unit": item.unit,
             "price_per_unit": item.price_per_unit, "status": item.status}
            for item in db.query(Product).filter(Product.farmer_id == current_user.id).all()
        ],
        "crop_plots": [
            {"id": item.id, "plot_name": item.plot_name, "crop_type": item.crop_type,
             "variety": item.variety, "planting_date": item.planting_date,
             "expected_harvest_date": item.expected_harvest_date,
             "crop_stage": item.crop_stage, "notes": item.notes}
            for item in db.query(CropPlot).filter(CropPlot.owner_id == current_user.id).all()
        ],
        "livestock": [
            {"id": item.id, "animal_name": item.animal_name,
             "animal_type": item.animal_type, "breed": item.breed,
             "tag_number": item.tag_number, "sex": item.sex,
             "service_date": item.service_date, "due_date": item.due_date,
             "status": item.status}
            for item in db.query(LivestockAnimal).filter(LivestockAnimal.owner_id == current_user.id).all()
        ],
        "farm_finance": [
            {"id": item.id, "transaction_type": item.transaction_type,
             "category": item.category, "amount": item.amount,
             "transaction_date": item.transaction_date,
             "description": item.description}
            for item in db.query(FarmTransaction).filter(FarmTransaction.owner_id == current_user.id).all()
        ],
    }


@router.delete("/me")
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id
    pending_wallet_transactions = (
        db.query(WalletTransaction.id)
        .filter(
            WalletTransaction.user_id == user_id,
            WalletTransaction.status == "pending",
        )
        .first()
    )
    if pending_wallet_transactions:
        raise HTTPException(
            status_code=409,
            detail="Resolve pending wallet transactions before deleting your account",
        )
    if wallet_balance_ugx(db, user_id) != 0:
        raise HTTPException(
            status_code=409,
            detail="Withdraw or spend your wallet balance before deleting your account",
        )
    db.query(AppReview).filter(AppReview.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(NotificationLog).filter(NotificationLog.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(WalletTransaction).filter(WalletTransaction.user_id == user_id).update(
        {WalletTransaction.user_id: None},
        synchronize_session=False,
    )
    db.query(CropPlot).filter(CropPlot.owner_id == user_id).delete(synchronize_session=False)
    db.query(LivestockAnimal).filter(LivestockAnimal.owner_id == user_id).delete(synchronize_session=False)
    db.query(FarmTransaction).filter(FarmTransaction.owner_id == user_id).delete(synchronize_session=False)
    db.query(Product).filter(Product.farmer_id == user_id).delete(synchronize_session=False)
    db.query(Farm).filter(Farm.owner_id == user_id).delete(synchronize_session=False)
    db.query(Order).filter(Order.buyer_id == user_id).delete(synchronize_session=False)
    db.delete(current_user)
    db.commit()
    return {"detail": "Account and associated records deleted"}
