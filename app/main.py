from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.admin import router as admin_router
from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.api.public import router as public_router
from app.api.stores import router as stores_router
from app.core.config import Settings
from app.core.security import security_headers
from app.core.views import APP_DIR

settings = Settings()
app = FastAPI(
    title="NFC Analytics",
    version="0.1.0",
    debug=False,
    docs_url=None if settings.environment == "production" else "/docs",
    redoc_url=None if settings.environment == "production" else "/redoc",
    openapi_url=None if settings.environment == "production" else "/openapi.json",
)
app.state.settings = settings
app.middleware("http")(security_headers)
app.include_router(health_router)
app.include_router(stores_router)
app.include_router(public_router)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

app.include_router(admin_router)
app.include_router(metrics_router)
settings.upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")
