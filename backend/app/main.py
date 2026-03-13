import uvicorn
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.middleware import LoggingMiddleware, RequestContextMiddleware
from app.core.logging_config import get_logger, setup_logging
from app.core.settings import settings
from app.routers.auth import router as auth_router
from app.routers.election import router as election_router
from app.routers.healthcheck import router as healthcheck_router
from app.routers.user import router as user_router
from app.routers.user_profile import router as user_profile_router
from app.routers.vote import router as vote_router

setup_logging()
logger = get_logger("app")

app = FastAPI(
    title="Election Backend",
    description="Backend for the Election System",
    version="0.1.0",
    docs_url="/docs",
)

logger.info("Application starting up...")

app.add_middleware(RequestContextMiddleware)
app.add_middleware(LoggingMiddleware)

cors_origins = settings.app_settings.CORS_ORIGINS
if cors_origins:
    cors_origins_list = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
else:
    cors_origins_list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

logger.info("Middleware configuration completed")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors and log details.
    """
    errors_detail = exc.errors()
    logger.warning(
        f"Validation error on {request.method} {request.url} | "
        f"Errors: {errors_detail}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors_detail},
    )


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(healthcheck_router, prefix="/health")
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(election_router, prefix="/elections")
api_router.include_router(vote_router, prefix="/votes")
api_router.include_router(user_router, prefix="/users")
api_router.include_router(user_profile_router, prefix="/user-profiles")

app.include_router(api_router)

logger.info("Routers configuration completed")

if __name__ == "__main__":
    logger.info(f"Starting application on {settings.app_settings.APP_HOST}:{settings.app_settings.APP_PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.app_settings.APP_HOST,
        port=settings.app_settings.APP_PORT,
        reload=False,
        workers=1,
    )