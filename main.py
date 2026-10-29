from fastapi import FastAPI

from core.exception_handlers import register_exception_handlers
from core.config import get_settings
from fastapi.middleware.cors import CORSMiddleware
from routers import sensor_devices
from routers.auth import router as auth_router
from routers.users import router as users_router

app = FastAPI(title="GridFit API")
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(sensor_devices.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Decision-support API that helps mini-grid operators check whether businesses fit within available power capacity."""
    return {"status": "ok"}
