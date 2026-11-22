"""
Seed script for Harvesta demo data.
Run: python seed_data.py
"""
from datetime import date, datetime, timezone, timedelta
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models import (
    User, Farm, Product, Order, OrderItem,
    DeliveryVan, Delivery, Shop, ShopInventory
)

# Create tables
Base.metadata.create_all(bind=engine)
db = SessionLocal()

def seed():
    print("Seeding Harvesta database...")

    # Clear existing (optional – comment out if you want to keep data)
    for model in [ShopInventory, Delivery, OrderItem, Order, Product, Farm, DeliveryVan, Shop, User]:
        db.query(model).delete()
    db.commit()

    # Users
    admin = User(
        email="admin@harvesta.com",
        full_name="Admin User",
        phone="+254700000001",
        role="admin",
        hashed_password=get_password_hash("admin123"),
    )
    farmer = User(
        email="farmer@harvesta.com",
        full_name="John Kamau",
        phone="+254712345678",
        role="farmer",
        hashed_password=get_password_hash("farmer123"),
    )
    driver = User(
        email="driver@harvesta.com",
        full_name="Peter Ochieng",
        phone="+254723456789",
        role="driver",
        hashed_password=get_password_hash("driver123"),
    )
    shop_mgr = User(
        email="shop@harvesta.com",
        full_name="Grace Wanjiku",
        phone="+254734567890",
        role="shop_manager",
        hashed_password=get_password_hash("shop123"),
    )
    buyer = User(
        email="buyer@harvesta.com",
        full_name="Mary Akinyi",
        phone="+254745678901",
        role="buyer",
        hashed_password=get_password_hash("buyer123"),
    )

    db.add_all([admin, farmer, driver, shop_mgr, buyer])
    db.commit()

    # Farm
    farm = Farm(
        owner_id=farmer.id,
        name="Green Valley Farm",
        location="Nakuru, Kenya",
        size_hectares=12.5,
        crop_types="maize,tomatoes,beans,kale",
        livestock="cattle,goats",
        description="Family-owned farm producing high-quality fresh produce and dairy.",
    )
    db.add(farm)
    db.commit()

    # Products
    products = [
        Product(
            farmer_id=farmer.id,
            farm_id=farm.id,
            name="Fresh Maize",
            category="crop",
            description="Sweet white maize, harvested this week",
            quantity=500,
            unit="kg",
            price_per_unit=45.0,
            harvest_date=date.today() - timedelta(days=3),
            status="available",
            image_url="https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=400",
        ),
        Product(
            farmer_id=farmer.id,
            farm_id=farm.id,
            name="Organic Tomatoes",
            category="crop",
            description="Vine-ripened organic tomatoes",
            quantity=200,
            unit="kg",
            price_per_unit=120.0,
            harvest_date=date.today() - timedelta(days=1),
            status="available",
            image_url="https://images.unsplash.com/photo-1546094096-0df4bcaaa337?w=400",
        ),
        Product(
            farmer_id=farmer.id,
            farm_id=farm.id,
            name="Kale (Sukuma Wiki)",
            category="crop",
            description="Fresh leafy greens",
            quantity=150,
            unit="bunches",
            price_per_unit=30.0,
            harvest_date=date.today(),
            status="available",
            image_url="https://images.unsplash.com/photo-1515543904379-3d757afe72e4?w=400",
        ),
        Product(
            farmer_id=farmer.id,
            farm_id=farm.id,
            name="Fresh Milk",
            category="livestock",
            description="Farm-fresh cow milk",
            quantity=80,
            unit="liters",
            price_per_unit=60.0,
            harvest_date=date.today(),
            status="available",
            image_url="https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400",
        ),
        Product(
            farmer_id=farmer.id,
            farm_id=farm.id,
            name="Free-range Eggs",
            category="livestock",
            description="Farm eggs from free-range chickens",
            quantity=300,
            unit="pieces",
            price_per_unit=15.0,
            harvest_date=date.today() - timedelta(days=2),
            status="available",
            image_url="https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=400",
        ),
    ]
    db.add_all(products)
    db.commit()

    # Delivery Van
    van = DeliveryVan(
        plate_number="KCA 123A",
        driver_id=driver.id,
        capacity_kg=1500,
        current_location="Nakuru Depot",
        status="available",
        brand_name="Harvesta",
    )
    db.add(van)
    db.commit()

    # Shop
    shop = Shop(
        name="Harvesta Fresh Market",
        manager_id=shop_mgr.id,
        location="Westlands, Nairobi",
        description="Your neighbourhood source of ultra-fresh farm produce",
        is_open=True,
        phone="+254711223344",
    )
    db.add(shop)
    db.commit()

    # Shop inventory (some products already stocked)
    inv = [
        ShopInventory(shop_id=shop.id, product_id=products[0].id, quantity=50, last_restocked=datetime.now(timezone.utc)),
        ShopInventory(shop_id=shop.id, product_id=products[1].id, quantity=30, last_restocked=datetime.now(timezone.utc)),
        ShopInventory(shop_id=shop.id, product_id=products[2].id, quantity=40, last_restocked=datetime.now(timezone.utc)),
    ]
    db.add_all(inv)
    db.commit()

    print("Seed completed successfully!")
    print("\nDemo accounts:")
    print("  Admin:        admin@harvesta.com   / admin123")
    print("  Farmer:       farmer@harvesta.com  / farmer123")
    print("  Driver:       driver@harvesta.com  / driver123")
    print("  Shop Manager: shop@harvesta.com    / shop123")
    print("  Buyer:        buyer@harvesta.com   / buyer123")

if __name__ == "__main__":
    seed()
    db.close()
