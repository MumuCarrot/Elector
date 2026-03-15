from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.core.logging_config import get_logger
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
) -> JSONResponse:
    """
    Create a new vote.
    """
    logger.info(
        f"Creating vote for election {vote_data.election_id} by user {current_user.id}"
    )

    vote = await vote_service.create_vote(vote_data, current_user.id)

    logger.info(f"Vote created successfully: {vote.id}")
    
    return JSONResponse(
        content=vote.model_dump(mode='json'), status_code=201
    )


@router.get("/user/{user_id}")
async def get_votes_by_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Get all votes by a specific user. Returns empty list if no votes.
    Users can only request their own votes.
    """
    
    if user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Can only access own votes")
    logger.info(f"Getting votes for user: {user_id}")

    votes = await vote_service.get_votes_by_user(user_id)
    return JSONResponse(content={"votes": [v.model_dump(mode="json") for v in votes]})


@router.get("/election/{election_id}/results")
async def get_results_by_election(
    election_id: str,
) -> JSONResponse:
    """
    Get all votes for a specific election.
    """
    logger.info(f"Getting votes for election: {election_id}")

    results = await vote_service.get_results_by_election(election_id)
    
    return JSONResponse(content=results)


@router.get("/election/{election_id}/my-vote")
async def get_my_vote_for_election(
    election_id: str,
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Get current user's vote for a specific election.
    """
    logger.info(
        f"Getting vote for election {election_id} by user {current_user.id}"
    )

    vote = await vote_service.get_user_vote_for_election(
        election_id, current_user.id
    )

    if not vote:
        from app.exceptions.user import VoteNotFoundError

        raise VoteNotFoundError(
            f"Vote for election {election_id} by user {current_user.id} not found"
        )

    return JSONResponse(content=vote.model_dump(mode='json'))
