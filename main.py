from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.exceptions import AppError
from routers.auth import router as auth_router
from routers.users import router as users_router
app = FastAPI(title="GridFit API", version="0.1.0")

app.include_router(auth_router)
app.include_router(users_router)

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.get("/health")
def health():
    return {"status": "ok"}
