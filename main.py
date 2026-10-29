from fastapi import FastAPI

from core.handlers import register_exception_handlers
from routers import (
    sensor_devices,
    site_profiles,
    sites,
)

from fastapi import Request
from fastapi.responses import JSONResponse

from core.exceptions import AppError
from routers import scenarios, meter_assignments
from routers.auth import router as auth_router


app = FastAPI(title="GridFit API")
register_exception_handlers(app)

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(auth_router)
app.include_router(sensor_devices.router)
app.include_router(site_profiles.router)
app.include_router(sites.router)


app.include_router(meter_assignments.router)
app.include_router(sensor_devices.router)
app.include_router(scenarios.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Decision-support API that helps mini-grid operators check whether businesses fit within available power capacity."""
    return {"status": "ok"}
