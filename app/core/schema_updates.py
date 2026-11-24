from sqlalchemy import Engine, inspect, text


_ADDITIVE_COLUMNS = {
    "users": {
        "notification_preference": "VARCHAR(10) NOT NULL DEFAULT 'email'",
    },
    "orders": {
        "payment_method": "VARCHAR(30) NOT NULL DEFAULT 'cash_on_delivery'",
        "payment_status": "VARCHAR(20) NOT NULL DEFAULT 'pending'",
        "payment_reference": "VARCHAR(100)",
    },
    "deliveries": {
        "driver_id": "INTEGER REFERENCES users(id)",
        "estimated_fee_ugx": "INTEGER NOT NULL DEFAULT 5000",
    },
}


def ensure_workflow_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)
        existing_tables = set(inspector.get_table_names())
        for table_name, columns in _ADDITIVE_COLUMNS.items():
            if table_name not in existing_tables:
                continue
            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            for column_name, definition in columns.items():
                if column_name not in existing_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} ADD COLUMN "
                            f"{column_name} {definition}"
                        )
                    )
                    existing_columns.add(column_name)
