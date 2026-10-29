from fastapi import FastAPI
from routers import meter_assignments, sensor_devices

from routers.auth import router as auth_router

app = FastAPI(title="GridFit API")


app.include_router(auth_router)

app.include_router(meter_assignments.router)
app.include_router(sensor_devices.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Decision-support API that helps mini-grid operators check whether businesses fit within available power capacity."""
    return {"status": "ok"}
