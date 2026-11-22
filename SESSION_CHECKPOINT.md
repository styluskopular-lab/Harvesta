# Harvesta Session Checkpoint

Saved: 2026-11-22

## Current state

- Uganda-first Harvesta application
- FastAPI backend and Streamlit frontend
- Asap typography and high-contrast Green/Grey/Black theme
- Gmail/phone registration and mandatory rules consent
- Farmer, buyer and driver roles
- Role-specific KYC fields
- Optional sub-county/parish and optional farm acreage
- Crop plots with days-based harvest calculations and growth stages
- Livestock reproduction tracker
- Farmer finance transactions, KPI cards and charts
- Account JSON/CSV export and account deletion
- UNFFE, NARO, MAAIF, MTIC and regulatory compliance pages

## How to resume

1. Open the Harvesta project folder.
2. Start the API:
   `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
3. Start the frontend:
   `python -m streamlit run streamlit_app/Home.py --server.port 8501`
4. Open `http://localhost:8501`.

## Files

- Backend: `app/`
- Frontend: `streamlit_app/`
- Database: `harvesta.db`
- Migration: `migrate_data.py`
