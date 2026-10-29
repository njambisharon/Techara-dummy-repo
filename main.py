from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.exceptions import AppError
from routers import (
    scenarios,
    sensor_devices,
)

from routers.auth import router as auth_router

app = FastAPI(title="GridFit API")


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(auth_router)


app.include_router(sensor_devices.router)
app.include_router(scenarios.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Decision-support API that helps mini-grid operators check whether businesses fit within available power capacity."""
    return {"status": "ok"}
