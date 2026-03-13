from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.dependencies.database import get_db
from app.dependencies.token import get_current_user
from app.models.user import User
from app.schemas.election import ElectionCreate, ElectionUpdate
from app.services.election import election_service

router = APIRouter(tags=["elections"])
logger = get_logger("election_router")


@router.post("", status_code=201)
async def create_election(
    election_data: ElectionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new election with candidates and settings.
    Requires authentication.
    """
    logger.info(f"Creating election: {election_data.title} by user: {current_user.id}")

    election = await election_service.create_election(
        session=session,
        election_data=election_data,
        current_user=current_user,
    )

    logger.info(f"Election created successfully: {election.id}")
    
    return JSONResponse(
        content=election.model_dump(mode='json'), status_code=201
    )


@router.get("")
async def get_all_elections(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get all elections with pagination.
    """
    logger.info(f"Getting all elections - page: {page}, page_size: {page_size}")

    elections = await election_service.get_all_elections(
        session, page=page, page_size=page_size
    )

    response_data = [election.model_dump(mode='json') for election in elections]
    
    return JSONResponse(content=response_data)


@router.get("/{election_id}")
async def get_election_by_id(
    election_id: str,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get election by ID.
    """
    logger.info(f"Getting election: {election_id}")

    election = await election_service.get_election_by_id(session, election_id)

    if not election:
        from app.exceptions.user import UserNotFoundError

        raise UserNotFoundError(f"Election with id {election_id} not found")

    return JSONResponse(content=election.model_dump(mode='json'))


@router.put("/{election_id}")
async def update_election(
    election_id: str,
    election_data: ElectionUpdate,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update election information.
    """
    logger.info(f"Updating election: {election_id}")

    election = await election_service.update_election(
        session, election_id, election_data
    )

    logger.info(f"Election updated successfully: {election.id}")
    
    return JSONResponse(content=election.model_dump(mode='json'))


@router.delete("/{election_id}")
async def delete_election(
    election_id: str,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete election by ID.
    """
    logger.info(f"Deleting election: {election_id}")

    await election_service.delete_election(session, election_id)

    logger.info(f"Election deleted successfully: {election_id}")
    
    return JSONResponse(
        content={"detail": f"Election with id {election_id} deleted successfully"},
        status_code=200,
    )
