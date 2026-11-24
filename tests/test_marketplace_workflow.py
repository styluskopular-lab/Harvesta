from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main
from app.core.database import Base, get_db
from app.core.schema_updates import ensure_workflow_schema
from app.services.marketplace_seed import seed_marketplace_if_empty
from sqlalchemy import inspect


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
                    "payment_method": "mobile_money",
                    "payment_reference": "MTN-UG-ORDER-12",
                },
            )
            assert order.status_code == 201, order.text
            order_data = order.json()
            assert order_data["total_amount"] == 7500
            assert order_data["items"][0]["product_name"] == "Maize"
            assert order_data["items"][0]["unit"] == "kg"
            assert order_data["payment_method"] == "mobile_money"
            assert order_data["payment_status"] == "pending"
            assert order_data["payment_reference"] == "MTN-UG-ORDER-12"
            assert order_data["delivery"]["status"] == "open"
            assert order_data["delivery"]["estimated_fee_ugx"] == 5000

            driver_registration = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "workflow.driver@gmail.com",
                    "full_name": "Workflow Driver",
                    "role": "driver",
                    "password": "driver-pass",
                    "privacy_consent": True,
                    "nin": "CM987654321098",
                    "date_of_birth": "1985-06-08",
                    "district": "Kampala",
                    "village": "Nakasero",
                    "next_of_kin_name": "Driver Contact",
                    "next_of_kin_contact": "+256700000003",
                    "driving_permit_number": "UG-DL-0001",
                    "driving_permit_class": "B",
                    "vehicle_type": "Pickup",
                    "vehicle_plate": "UAA 123A",
                    "goods_insurance_status": "active",
                },
            )
            assert driver_registration.status_code == 201, driver_registration.text
            driver_headers = {
                "Authorization": f"Bearer {driver_registration.json()['access_token']}"
            }

            open_deliveries = client.get(
                "/api/v1/deliveries/open",
                headers=driver_headers,
            )
            assert open_deliveries.status_code == 200
            delivery = next(
                item
                for item in open_deliveries.json()
                if item["order_id"] == order_data["id"]
            )
            assert delivery["pickup_district"] == "Wakiso"
            assert delivery["delivery_district"] == "Kampala"
            assert delivery["items"] == [
                {
                    "product_name": "Maize",
                    "quantity": 3,
                    "unit": "kg",
                    "pickup_district": "Wakiso",
                }
            ]
            assert delivery["estimated_fee_ugx"] == 5000

            accepted = client.post(
                f"/api/v1/deliveries/{delivery['id']}/accept",
                headers=driver_headers,
            )
            assert accepted.status_code == 200, accepted.text
            assert accepted.json()["status"] == "accepted"
            assert accepted.json()["driver_name"] == "Workflow Driver"
            assert accepted.json()["driver_id"] == driver_registration.json()["id"]
            cannot_accept_twice = client.post(
                f"/api/v1/deliveries/{delivery['id']}/accept",
                headers=driver_headers,
            )
            assert cannot_accept_twice.status_code == 409

            cannot_skip_status = client.patch(
                f"/api/v1/deliveries/{delivery['id']}",
                headers=driver_headers,
                json={"status": "in_transit"},
            )
            assert cannot_skip_status.status_code == 409

            for next_status in ("picked_up", "in_transit", "delivered"):
                updated_delivery = client.patch(
                    f"/api/v1/deliveries/{delivery['id']}",
                    headers=driver_headers,
                    json={"status": next_status},
                )
                assert updated_delivery.status_code == 200, updated_delivery.text
                assert updated_delivery.json()["status"] == next_status

            buyer_orders = client.get("/api/v1/orders/", headers=buyer_headers)
            assert buyer_orders.status_code == 200
            assert [item["id"] for item in buyer_orders.json()] == [order_data["id"]]
            assert buyer_orders.json()[0]["delivery"]["status"] == "delivered"
            assert buyer_orders.json()[0]["delivery"]["driver_name"] == "Workflow Driver"

            farmer_orders = client.get("/api/v1/orders/", headers=farmer_headers)
            assert farmer_orders.status_code == 200
            assert farmer_orders.json()[0]["delivery"]["status"] == "delivered"
            assert farmer_orders.json()[0]["delivery"]["driver_name"] == "Workflow Driver"

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
            assert incoming_orders.json()[0]["payment_status"] == "pending"
            assert incoming_orders.json()[0]["delivery"]["status"] == "delivered"

            for headers_for_role in (buyer_headers, farmer_headers, driver_headers):
                visible_deliveries = client.get(
                    "/api/v1/deliveries/",
                    headers=headers_for_role,
                )
                assert visible_deliveries.status_code == 200
                assert any(
                    item["id"] == delivery["id"]
                    and item["status"] == "delivered"
                    and item["driver_name"] == "Workflow Driver"
                    for item in visible_deliveries.json()
                )

            shop_manager_registration = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "workflow.manager@gmail.com",
                    "full_name": "Workflow Manager",
                    "role": "shop_manager",
                    "password": "manager-pass",
                    "privacy_consent": True,
                    "nin": "CF987654321098",
                    "date_of_birth": "1980-02-20",
                    "district": "Kampala",
                    "village": "Central",
                    "next_of_kin_name": "Manager Contact",
                    "next_of_kin_contact": "+256700000004",
                },
            )
            assert shop_manager_registration.status_code == 201
            manager_headers = {
                "Authorization": f"Bearer {shop_manager_registration.json()['access_token']}"
            }
            buyer_cannot_confirm_payment = client.patch(
                f"/api/v1/orders/{order_data['id']}/payment",
                headers=buyer_headers,
                json={},
            )
            assert buyer_cannot_confirm_payment.status_code == 403
            confirmed_payment = client.patch(
                f"/api/v1/orders/{order_data['id']}/payment",
                headers=manager_headers,
                json={},
            )
            assert confirmed_payment.status_code == 200, confirmed_payment.text
            assert confirmed_payment.json()["payment_status"] == "paid"
            assert confirmed_payment.json()["payment_reference"] == "MTN-UG-ORDER-12"

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


def test_ensure_workflow_schema_adds_missing_columns_idempotently():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql("CREATE TABLE users (id INTEGER PRIMARY KEY)")
            connection.exec_driver_sql("CREATE TABLE orders (id INTEGER PRIMARY KEY)")
            connection.exec_driver_sql(
                "CREATE TABLE deliveries (id INTEGER PRIMARY KEY, order_id INTEGER)"
            )

        ensure_workflow_schema(engine)
        ensure_workflow_schema(engine)

        inspector = inspect(engine)
        assert {
            "payment_method",
            "payment_status",
            "payment_reference",
        } <= {column["name"] for column in inspector.get_columns("orders")}
        assert {
            "driver_id",
            "estimated_fee_ugx",
        } <= {column["name"] for column in inspector.get_columns("deliveries")}
    finally:
        engine.dispose()
