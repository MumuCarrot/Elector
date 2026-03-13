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
    """
    Root endpoint for health checks.
    """
    logger.info(f"Health check requested")

    response_data = {"status_code": 200, "detail": "ok", "result": "working"}
    logger.info(f"Health check completed successfully")

    return JSONResponse(content=response_data)


@router.get("/postgresql")
async def health_db():
    """
    PostgreSQL database health check endpoint.
    """
    logger.info(f"Health check for PostgreSQL requested")

    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            if result.scalar() == 1:
                return JSONResponse(content={"status": "ok"})
            else:
                return JSONResponse(
                    content={"status": "error", "detail": "Unexpected result from DB"}
                )
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)})


@router.get("/redis")
async def health_redis():
    """
    Redis database health check endpoint.
    """
    logger.info(f"Health check for Redis requested")

    try:
        pong = await redis_client.ping()
        await redis_client.close()

        if pong:
            return JSONResponse(content={"status": "ok", "detail": "Redis is healthy"})
        else:
            return JSONResponse(
                content={"status": "error", "detail": "Redis did not respond with PONG"}
            )
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)})


@router.get("/protected")
async def protected_endpoint(
    auth: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Protected endpoint that requires a valid JWT token.
    """
    logger.info(f"Protected endpoint accessed")

    return JSONResponse(
        content={
            "message": "Authentication successful!",
            "authenticated": True,
            "user_id": auth.id,
            "user_login": auth.login,
        }
    )