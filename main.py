from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import get_settings
from core.exceptions import AppError
from core.handlers import register_exception_handlers
from routers import (
    meter_assignments,
    scenarios,
    sensor_devices,
    site_profiles,
    sites,
)
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


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(sensor_devices.router)
app.include_router(site_profiles.router)
app.include_router(sites.router)
app.include_router(meter_assignments.router)
app.include_router(scenarios.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Decision-support API that helps mini-grid operators check whether businesses fit within available power capacity."""
    return {"status": "ok"}
