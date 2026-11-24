import secrets

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.product import Product
from app.models.user import User


DEMO_LISTINGS = [
    {
        "email": "marketplace.kampala@harvesta.ug",
        "farmer": "Sarah Nakato",
        "district": "Kampala",
        "product": "Matooke",
        "quantity": 80,
        "unit": "bunches",
        "price": 18000,
        "description": "Fresh green matooke harvested this week.",
    },
    {
        "email": "marketplace.masaka@harvesta.ug",
        "farmer": "Joseph Ssemanda",
        "district": "Masaka",
        "product": "Maize",
        "quantity": 250,
        "unit": "kg",
        "price": 2200,
        "description": "Dried, clean maize grain from Masaka.",
    },
    {
        "email": "marketplace.mbale@harvesta.ug",
        "farmer": "Aisha Wekesa",
        "district": "Mbale",
        "product": "Arabica Coffee",
        "quantity": 60,
        "unit": "kg",
        "price": 14500,
        "description": "Locally grown Arabica coffee beans.",
    },
    {
        "email": "marketplace.mbarara@harvesta.ug",
        "farmer": "David Tumusiime",
        "district": "Mbarara",
        "product": "Irish Potatoes",
        "quantity": 180,
        "unit": "kg",
        "price": 3500,
        "description": "Freshly harvested Irish potatoes.",
    },
    {
        "email": "marketplace.gulu@harvesta.ug",
        "farmer": "Grace Acen",
        "district": "Gulu",
        "product": "Beans",
        "quantity": 120,
        "unit": "kg",
        "price": 4800,
        "description": "Sorted and dried beans from Northern Uganda.",
    },
]


def seed_marketplace_if_empty(db: Session) -> int:
    if db.query(Product.id).filter(Product.status == "available").first():
        return 0

    seeded = 0
    for listing in DEMO_LISTINGS:
        farmer = db.query(User).filter(User.email == listing["email"]).first()
        if farmer is None:
            farmer = User(
                email=listing["email"],
                full_name=listing["farmer"],
                role="farmer",
                district=listing["district"],
                location_name=f"{listing['district']}, Uganda",
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
            )
            db.add(farmer)
            db.flush()

        product = Product(
            farmer_id=farmer.id,
            name=listing["product"],
            category="crop",
            description=listing["description"],
            quantity=listing["quantity"],
            unit=listing["unit"],
            price_per_unit=listing["price"],
            status="available",
        )
        db.add(product)
        seeded += 1

    db.commit()
    return seeded
