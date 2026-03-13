from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.dependencies.database import get_db
from app.dependencies.token import get_current_user
from app.models.user import User
from app.schemas.vote import VoteCreate, VoteUpdate
from app.services.vote import vote_service

router = APIRouter(tags=["votes"])
logger = get_logger("vote_router")


@router.post("", status_code=201)
async def create_vote(
    vote_data: VoteCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new vote.
    """
    logger.info(
        f"Creating vote for election {vote_data.election_id} by user {current_user.id}"
    )

    vote = await vote_service.create_vote(session, vote_data, current_user)

    logger.info(f"Vote created successfully: {vote.id}")
    
    return JSONResponse(
        content=vote.model_dump(mode='json'), status_code=201
    )


@router.get("")
async def get_all_votes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get all votes with pagination.
    """
    logger.info(f"Getting all votes - page: {page}, page_size: {page_size}")

    votes = await vote_service.get_all_votes(session, page=page, page_size=page_size)

    response_data = [vote.model_dump(mode='json') for vote in votes]
    
    return JSONResponse(content=response_data)


@router.get("/{vote_id}")
async def get_vote_by_id(
    vote_id: str,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get vote by ID.
    """
    logger.info(f"Getting vote: {vote_id}")

    vote = await vote_service.get_vote_by_id(session, vote_id)

    if not vote:
        from app.exceptions.user import VoteNotFoundError

        raise VoteNotFoundError(f"Vote with id {vote_id} not found")

    return JSONResponse(content=vote.model_dump(mode='json'))


@router.get("/election/{election_id}")
async def get_votes_by_election(
    election_id: str,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get all votes for a specific election.
    """
    logger.info(f"Getting votes for election: {election_id}")

    votes = await vote_service.get_votes_by_election(session, election_id)

    response_data = [vote.model_dump(mode='json') for vote in votes]
    
    return JSONResponse(content=response_data)


@router.get("/user/{user_id}")
async def get_votes_by_user(
    user_id: str,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get all votes by a specific user.
    """
    logger.info(f"Getting votes for user: {user_id}")

    votes = await vote_service.get_votes_by_user(session, user_id)

    response_data = [vote.model_dump(mode='json') for vote in votes]
    
    return JSONResponse(content=response_data)


@router.get("/election/{election_id}/my-vote")
async def get_my_vote_for_election(
    election_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get current user's vote for a specific election.
    """
    logger.info(
        f"Getting vote for election {election_id} by user {current_user.id}"
    )

    vote = await vote_service.get_user_vote_for_election(
        session, election_id, current_user.id
    )

    if not vote:
        from app.exceptions.user import VoteNotFoundError

        raise VoteNotFoundError(
            f"Vote for election {election_id} by user {current_user.id} not found"
        )

    return JSONResponse(content=vote.model_dump(mode='json'))


@router.put("/{vote_id}")
async def update_vote(
    vote_id: str,
    vote_data: VoteUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update vote information.
    """
    logger.info(f"Updating vote: {vote_id}")

    vote = await vote_service.update_vote(session, vote_id, vote_data, current_user)

    logger.info(f"Vote updated successfully: {vote.id}")
    
    return JSONResponse(content=vote.model_dump(mode='json'))


@router.delete("/{vote_id}")
async def delete_vote(
    vote_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete vote by ID.
    """
    logger.info(f"Deleting vote: {vote_id}")

    await vote_service.delete_vote(session, vote_id, current_user)

    logger.info(f"Vote deleted successfully: {vote_id}")
    
    return JSONResponse(
        content={"detail": f"Vote with id {vote_id} deleted successfully"},
        status_code=200,
    )
