from datetime import date, datetime, timezone, timedelta

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models import *


Base.metadata.create_all(bind=engine)
db = SessionLocal()


def add_uganda_seed():
    for model in [
        VetBooking, Veterinarian, ShopInventory, Delivery, OrderItem, Order,
        Product, Farm, DeliveryVan, Shop, User,
    ]:
        db.query(model).delete()
    db.commit()

    users = [
        User(email="buyer@harvesta.ug", full_name="Nalubiri Sarah", phone="+256701234567",
             role="buyer", location_name="Kololo, Kampala",
             latitude=0.335, longitude=32.600, hashed_password=get_password_hash("buyer123")),
        User(email="farmer@harvesta.ug", full_name="John Okello", phone="+256772345678",
             role="farmer", location_name="Mukono", latitude=0.355,
             longitude=32.755, hashed_password=get_password_hash("farmer123")),
        User(email="driver@harvesta.ug", full_name="Peter Mugisha", phone="+256783456789",
             role="driver", location_name="Kampala", latitude=0.3476,
             longitude=32.5825, hashed_password=get_password_hash("driver123")),
        User(email="shop@harvesta.ug", full_name="Grace Namatovu", phone="+256704567890",
             role="shop_manager", location_name="Kampala", latitude=0.3476,
             longitude=32.5825, hashed_password=get_password_hash("shop123")),
    ]
    db.add_all(users)
    db.commit()
    farmer = users[1]

    farm = Farm(
        owner_id=farmer.id, name="Okello Green Acres", location="Mukono, Uganda",
        size_hectares=8.5, crop_types="matooke,beans,maize",
        livestock="goats,cattle,chicken",
        latitude=0.355, longitude=32.755,
        description="Uganda-grown food for local families.",
    )
    db.add(farm)
    db.commit()

    products = [
        ("Matooke", "crop", "Fresh green matooke bunch", 85, "bunches", 18000,
         "https://images.unsplash.com/photo-1603833665858-e61d17a86224?w=700"),
        ("Fresh Milk", "processed", "Fresh Ugandan milk", 120, "liters", 2600,
         "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=700"),
        ("Maganjo Wheat Flour", "processed", "Premium Ugandan wheat flour", 200, "kg", 5500,
         "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=700"),
        ("Mukwano Sunflower Oil", "processed", "Locally packed cooking oil", 90, "liters", 12000,
         "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=700"),
        ("Ntake Bread", "processed", "Fresh Ugandan baked bread", 150, "pieces", 5500,
         "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=700"),
        ("Goat Meat", "livestock", "Fresh local goat meat", 60, "kg", 28000,
         "https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=700"),
        ("Free-range Eggs", "livestock", "Ugandan free-range eggs", 300, "pieces", 900,
         "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=700"),
        ("Irish Potatoes", "crop", "Fresh Ugandan Irish potatoes", 250, "kg", 4200,
         "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=700"),
    ]
    seed_products = [
        Product(farmer_id=farmer.id, farm_id=farm.id, name=name, category=category,
                description=description, quantity=quantity, unit=unit,
                price_per_unit=price, harvest_date=date.today(),
                status="available", image_url=image)
        for name, category, description, quantity, unit, price, image in products
    ]
    db.add_all(seed_products)

    providers = [
        Veterinarian(name="Dr. Namara Claire", phone="+256772111222",
                     specialization="Cattle and large-animal care", district="Mukono",
                     latitude=0.36, longitude=32.75, is_available=True,
                     description="Farm visits and livestock treatment."),
        Veterinarian(name="Dr. Kato Samuel", phone="+256701222333",
                     specialization="Goat and poultry health", district="Kampala",
                     latitude=0.3476, longitude=32.5825, is_available=True,
                     description="Goats, poultry and vaccination support."),
        Veterinarian(name="Dr. Atim Mercy", phone="+256783333444",
                     specialization="Small-animal and dairy care", district="Entebbe",
                     latitude=0.064, longitude=32.446, is_available=True,
                     description="Dairy, goats and household animal care."),
    ]
    db.add_all(providers)

    van = DeliveryVan(
        plate_number="UAX 123A", driver_id=users[2].id, capacity_kg=1500,
        current_location="Mukono Depot", status="available",
        brand_name="Harvesta Uganda",
    )
    db.add(van)

    shop = Shop(name="Harvesta Fresh Market Uganda", manager_id=users[3].id,
                location="Kololo, Kampala",
                description="Ugandan produce and everyday local brands",
                is_open=True, phone="+256704567890")
    db.add(shop)
    db.commit()

    print("Uganda MVP seed complete")
    print("Buyer: buyer@harvesta.ug / buyer123")
    print("Farmer: farmer@harvesta.ug / farmer123")


if __name__ == "__main__":
    add_uganda_seed()
    db.close()
