from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main
from app.core.database import Base, get_db
from app.services.marketplace_seed import seed_marketplace_if_empty


def test_farmer_listing_buyer_order_and_incoming_order(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_sessions = sessionmaker(autoflush=False, autocommit=False, bind=engine)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main, "SessionLocal", test_sessions)

    def override_get_db():
        db = test_sessions()
        try:
            yield db
        finally:
            db.close()

    Base.metadata.drop_all(bind=engine)
    main.app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(main.app) as client:
            marketplace = client.get("/api/v1/products/")
            assert marketplace.status_code == 200
            seeded_listings = marketplace.json()
            assert len(seeded_listings) == 5
            assert {item["farmer_location"] for item in seeded_listings} >= {
                "Kampala, Uganda",
                "Masaka, Uganda",
                "Mbale, Uganda",
                "Mbarara, Uganda",
            }

            with test_sessions() as db:
                assert seed_marketplace_if_empty(db) == 0

            farmer_registration = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "workflow.farmer@gmail.com",
                    "full_name": "Workflow Farmer",
                    "role": "farmer",
                    "password": "farmer-pass",
                    "privacy_consent": True,
                    "nin": "CM123456789012",
                    "date_of_birth": "1988-04-12",
                    "district": "Wakiso",
                    "village": "Nansana",
                    "next_of_kin_name": "Farmer Contact",
                    "next_of_kin_contact": "+256700000001",
                    "primary_farm_enterprise": "Crops",
                },
            )
            assert farmer_registration.status_code == 201, farmer_registration.text
            farmer_token = farmer_registration.json()["access_token"]
            farmer_headers = {"Authorization": f"Bearer {farmer_token}"}

            product = client.post(
                "/api/v1/products/",
                headers=farmer_headers,
                json={
                    "name": "Maize",
                    "category": "crop",
                    "quantity": 100,
                    "unit": "kg",
                    "price_per_unit": 2500,
                    "status": "available",
                },
            )
            assert product.status_code == 201, product.text
            listed_product = product.json()
            assert listed_product["farmer_location"] == "Wakiso"
            assert listed_product["price_per_unit"] == 2500

            farmer_products = client.get(
                "/api/v1/products/farmer/me",
                headers=farmer_headers,
            )
            assert farmer_products.status_code == 200
            assert any(item["id"] == listed_product["id"] for item in farmer_products.json())

            buyer_registration = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "workflow.buyer@gmail.com",
                    "full_name": "Workflow Buyer",
                    "role": "buyer",
                    "password": "buyer-pass",
                    "privacy_consent": True,
                    "nin": "CF123456789012",
                    "date_of_birth": "1992-08-03",
                    "district": "Kampala",
                    "village": "Nakawa",
                    "next_of_kin_name": "Buyer Contact",
                    "next_of_kin_contact": "+256700000002",
                },
            )
            assert buyer_registration.status_code == 201, buyer_registration.text
            buyer_headers = {
                "Authorization": f"Bearer {buyer_registration.json()['access_token']}"
            }

            order = client.post(
                "/api/v1/orders/",
                headers=buyer_headers,
                json={
                    "items": [{"product_id": listed_product["id"], "quantity": 3}],
                    "delivery_address": "Nakawa, Kampala, Uganda",
                },
            )
            assert order.status_code == 201, order.text
            order_data = order.json()
            assert order_data["total_amount"] == 7500
            assert order_data["items"][0]["product_name"] == "Maize"
            assert order_data["items"][0]["unit"] == "kg"

            buyer_orders = client.get("/api/v1/orders/", headers=buyer_headers)
            assert buyer_orders.status_code == 200
            assert [item["id"] for item in buyer_orders.json()] == [order_data["id"]]

            incoming_orders = client.get(
                "/api/v1/orders/incoming",
                headers=farmer_headers,
            )
            assert incoming_orders.status_code == 200
            assert incoming_orders.json()[0]["items"] == [
                {
                    "product_id": listed_product["id"],
                    "product_name": "Maize",
                    "quantity": 3,
                    "unit": "kg",
                    "unit_price": 2500,
                    "subtotal": 7500,
                }
            ]

            remaining_product = client.get(
                f"/api/v1/products/{listed_product['id']}"
            )
            assert remaining_product.json()["quantity"] == 97

            farmer_cannot_order = client.post(
                "/api/v1/orders/",
                headers=farmer_headers,
                json={
                    "items": [{"product_id": listed_product["id"], "quantity": 1}],
                    "delivery_address": "Kampala, Uganda",
                },
            )
            assert farmer_cannot_order.status_code == 403
    finally:
        main.app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
