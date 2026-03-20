from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.logging_config import get_logger
from app.db.database import async_session_maker
from app.db.redis_client import redis_client
from app.dependencies.token import get_current_user
from app.models import User

router = APIRouter()
logger = get_logger("healthcheck")


@router.get("/")
def healthcheck() -> JSONResponse:
    """Lightweight liveness probe without external dependencies.

    Returns:
        JSONResponse: Static OK payload.

    """
    logger.info("Health check requested")

    response_data = {"status_code": 200, "detail": "ok", "result": "working"}
    logger.info("Health check completed successfully")

    return JSONResponse(content=response_data)


@router.get("/postgresql")
async def health_db():
    """Runs ``SELECT 1`` through the async SQLAlchemy engine.

    Returns:
        JSONResponse: ``{"status": "ok"}`` or error detail on failure.

    """
    logger.info("Health check for PostgreSQL requested")

    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            if result.scalar() == 1:
                return JSONResponse(content={"status": "ok"})
            return JSONResponse(
                content={"status": "error", "detail": "Unexpected result from DB"}
            )
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)})


@router.get("/redis")
async def health_redis():
    """Pings the shared async Redis client.

    Returns:
        JSONResponse: OK when PONG received.

    """
    logger.info("Health check for Redis requested")

    try:
        pong = await redis_client.ping()
        await redis_client.close()

        if pong:
            return JSONResponse(content={"status": "ok", "detail": "Redis is healthy"})
        return JSONResponse(
            content={"status": "error", "detail": "Redis did not respond with PONG"}
        )
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)})


@router.get("/protected")
async def protected_endpoint(
    auth: User = Depends(get_current_user),
) -> JSONResponse:
    """Smoke test for cookie JWT auth (requires valid ``access_token``).

    Args:
        auth: Injected authenticated user.

    Returns:
        JSONResponse: Minimal identity echo.

    """
    logger.info("Protected endpoint accessed")

    return JSONResponse(
        content={
            "message": "Authentication successful!",
            "authenticated": True,
            "user_id": auth.id,
            "user_email": auth.email,
        }
    )
