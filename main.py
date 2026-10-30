from fastapi import FastAPI

from core.handlers import register_exception_handlers
from routers import (
    readings,
    businesses,
    meter_assignments,
    scenarios,
    sensor_devices,
    site_profiles,
    sites,
)
from routers.auth import router as auth_router

app = FastAPI(title="GridFit API")
register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(meter_assignments.router)
app.include_router(sensor_devices.router)
app.include_router(scenarios.router)
app.include_router(businesses.router)
app.include_router(sites.router)
app.include_router(site_profiles.router)
app.include_router(readings.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
