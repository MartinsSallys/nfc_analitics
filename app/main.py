from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.stores import router as stores_router

app = FastAPI(title="NFC Analytics", version="0.1.0")
app.include_router(health_router)
app.include_router(stores_router)
