from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """Returns a static OK payload.

    Returns:
        dict: ``{"status": "ok"}``.

    """
    return {"status": "ok"}
