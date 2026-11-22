from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import auth, products, orders, farms, deliveries, shops, weather, veterinary, farm_records, farm_finance

# Import all models so Base knows about them
from app.models import *  # noqa: F401, F403


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown (if needed)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Harvesta – Farm-to-Table Agri-Tech Platform API",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(farms.router, prefix="/api/v1")
app.include_router(deliveries.router, prefix="/api/v1")
app.include_router(shops.router, prefix="/api/v1")
app.include_router(weather.router, prefix="/api/v1")
app.include_router(veterinary.router, prefix="/api/v1")
app.include_router(farm_records.router, prefix="/api/v1")
app.include_router(farm_finance.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "Welcome to Harvesta API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.APP_NAME}
