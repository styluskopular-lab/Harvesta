from sqlalchemy import inspect, text

from app.core.database import engine, Base
from app.models import *


Base.metadata.create_all(bind=engine)
columns = {column["name"] for column in inspect(engine).get_columns("users")}

kyc_columns = {
    "nin": "VARCHAR(14)",
    "date_of_birth": "DATE",
    "district": "VARCHAR(100)",
    "subcounty": "VARCHAR(100)",
    "village": "VARCHAR(100)",
    "next_of_kin_name": "VARCHAR(150)",
    "next_of_kin_contact": "VARCHAR(30)",
    "primary_farm_enterprise": "VARCHAR(30)",
    "farm_size_acres": "FLOAT",
    "dfa_cooperative_id": "VARCHAR(100)",
    "driving_permit_number": "VARCHAR(100)",
    "driving_permit_class": "VARCHAR(30)",
    "vehicle_type": "VARCHAR(30)",
    "vehicle_plate": "VARCHAR(30)",
    "goods_insurance_status": "VARCHAR(50)",
}
if "expected_harvest_days" not in {column["name"] for column in inspect(engine).get_columns("crop_plots")}:
    pass
columns = {column["name"] for column in inspect(engine).get_columns("users")}

with engine.begin() as connection:
    if "expected_harvest_days" not in {column["name"] for column in inspect(engine).get_columns("crop_plots")}:
        connection.execute(text("ALTER TABLE crop_plots ADD COLUMN expected_harvest_days INTEGER"))
    for column_name, column_type in kyc_columns.items():
        if column_name not in columns:
            connection.execute(
                text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
            )
    if "privacy_consent" not in columns:
        connection.execute(
            text("ALTER TABLE users ADD COLUMN privacy_consent BOOLEAN NOT NULL DEFAULT 0")
        )
    if "privacy_consent_at" not in columns:
        connection.execute(
            text("ALTER TABLE users ADD COLUMN privacy_consent_at DATETIME")
        )
    connection.execute(
        text(
            "UPDATE products SET name = 'Fresh Milk', "
            "description = 'Fresh Ugandan milk' "
            "WHERE name LIKE '%Lato%' OR description LIKE '%Lato%'"
        )
    )

print("Database migration complete")
