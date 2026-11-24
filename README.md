# Harvesta

**Farm-to-Table Agri-Tech Platform**

A complete Python full-stack platform inspired by the Harvesta concept:
- Farmer mobile-style portal (manage farms, products, harvests)
- Marketplace for produce
- Delivery logistics with branded vans
- Fresh produce shop management

## Features

- JWT Authentication with roles: `farmer`, `driver`, `shop_manager`, `admin`
- Farm & Product management
- Marketplace browsing & ordering
- Delivery tracking
- Shop inventory
- Beautiful Streamlit multi-page frontend (green theme)

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 + Pydantic v2
- **Auth**: JWT (python-jose + passlib)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Streamlit
- **Migrations**: Alembic

## Quick Start

### 1. Clone & Setup

```bash
cd harvesta
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-backend.txt -r requirements.txt
cp .env.example .env
```

Set `JWT_SECRET_KEY` in `.env` to a long random value. `DATABASE_URL` can be a
local SQLite URL for development or a hosted PostgreSQL URL for deployment.

### 2. Initialize Database

Database tables are created automatically when the API starts. If there are no
available marketplace listings, the API seeds five sample Ugandan produce
listings with seller districts. To reset or load the full local demo dataset:

```bash
python seed_data.py
```

### 3. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### 4. Run the Streamlit Frontend

```bash
streamlit run streamlit_app/Home.py
```

Frontend: http://localhost:8501

## Cloud Deployment

- Deploy the API from this directory using `render.yaml`. Set `DATABASE_URL` to
  the connection URL from Neon or Supabase; Render generates `JWT_SECRET_KEY`.
- Deploy `streamlit_app/Home.py` to Streamlit Community Cloud and set the
  `BACKEND_API_URL` secret to the Render service URL (without `/api/v1`).
- Render's free web services sleep after inactivity, so they do not provide
  uninterrupted 24/7 availability.

## Project Structure

```
harvesta/
├── app/
│   ├── main.py              # FastAPI entrypoint
│   ├── core/                # Config, DB, Security
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/v1/              # API routers
│   └── services/            # Business logic
├── streamlit_app/           # Multi-page Streamlit UI
├── alembic/                 # Migrations
├── tests/
├── requirements.txt
├── .env.example
└── seed_data.py
```

## Default Demo Accounts (after seeding)

| Role          | Email                 | Password   |
|---------------|-----------------------|------------|
| Admin         | admin@harvesta.com    | admin123   |
| Farmer        | farmer@harvesta.com   | farmer123  |
| Driver        | driver@harvesta.com   | driver123  |
| Shop Manager  | shop@harvesta.com     | shop123    |

## API Overview

- `POST /api/v1/auth/register` – Create account
- `POST /api/v1/auth/login` – Get tokens
- `GET  /api/v1/auth/me` – Current user
- `GET  /api/v1/products` – Marketplace
- `POST /api/v1/products` – Create product (farmer)
- `GET  /api/v1/orders` – List orders
- `POST /api/v1/orders` – Place order
- `GET  /api/v1/deliveries` – Track deliveries

## License

MIT – Built for learning and rapid prototyping.
