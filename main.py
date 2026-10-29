from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.exceptions import AppError
from routers import businesses, meter_assignments, scenarios, sensor_devices
from routers.auth import router as auth_router

app = FastAPI(title="GridFit API")


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


app.include_router(auth_router)
app.include_router(meter_assignments.router)
app.include_router(sensor_devices.router)
app.include_router(scenarios.router)
app.include_router(businesses.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
