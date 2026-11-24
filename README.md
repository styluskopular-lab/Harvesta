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
- Driver delivery board with atomic job claiming and step-by-step status updates
- Checkout methods: Harvesta Wallet, MTN / Airtel Mobile Money, Visa / Mastercard,
  PayPal, and Cash on Delivery
- UGX wallet ledger with pending external deposits/withdrawals and manual admin
  verification
- Checkout and wallet fee estimates, with farmer proceeds, service fees and tax
  estimate entries recorded in the ledger
- One-week app rating prompt and user-selected email/SMS notification channels
- Shop inventory
- Beautiful Streamlit multi-page frontend (green theme)

New marketplace orders automatically open a delivery job with an estimated flat
fee of UGX 5,000. Drivers can accept it, then update it through Picked Up,
In Transit, and Delivered. Buyers, farmers, and assigned drivers can see the
delivery status and driver details. Mobile Money references are recorded on the
order; an admin or shop manager confirms payment after verification.

On startup, the API creates all SQLAlchemy tables and adds missing payment,
driver-assignment, and notification-preference columns to existing tables.

External payment methods are recorded as pending requests; Harvesta does not
charge cards, initiate Mobile Money collections, or issue payouts without a
configured provider integration. Administrators manually verify order payments
and wallet deposits/withdrawals. The current model uses a 5% service fee on
completed farmer proceeds, estimated 18% VAT on that fee, and an estimated 0.5%
withdrawal levy. These values are configurable backend constants and are
estimates only, not tax or regulatory advice. Deposits currently have no
Harvesta service fee or estimated tax.

Notification preferences can be Email, SMS, or both. Configure SMTP using
`SMTP_HOST`, `SMTP_USER`, and `SMTP_PASS`. SMS can use Africa's Talking
(`AT_USERNAME`, `AT_API_KEY`, optional `AT_SENDER_ID`) or Twilio
(`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`). If a provider
is not configured, notification events are stored in `notification_logs`.

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
- `POST /api/v1/orders/quote` – Quote checkout fees and estimated taxes
- `GET  /api/v1/deliveries` – Track deliveries
- `GET  /api/v1/deliveries/open` – Driver job board
- `POST /api/v1/deliveries/{id}/accept` – Claim an open delivery
- `PATCH /api/v1/deliveries/{id}` – Advance an assigned delivery status
- `PATCH /api/v1/orders/{id}/payment` – Confirm payment (admin/shop manager)
- `GET /api/v1/wallet` – Wallet balance and transaction ledger
- `POST /api/v1/wallet/quote` – Quote a deposit or withdrawal
- `POST /api/v1/wallet/deposits` – Record a pending wallet deposit
- `POST /api/v1/wallet/withdrawals` – Request a pending wallet withdrawal
- `GET /api/v1/reviews/prompt` and `POST /api/v1/reviews` – Rating prompt and review

## License

MIT – Built for learning and rapid prototyping.
