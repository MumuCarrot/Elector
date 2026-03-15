import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.dependencies.database import get_db
from app.dependencies.token import get_current_user
from app.models.election_setting import ElectionSetting
from app.models.user import User
from app.repository.anonymous_vote_token_repository import AnonymousVoteTokenRepository
from app.repository.election_setting_repository import ElectionSettingRepository
from app.schemas.vote import VoteCreate, VoteUpdate, VoteBatchCreate
from app.services.vote import vote_service

router = APIRouter(tags=["votes"])
logger = get_logger("vote_router")


@router.post("/election/{election_id}/request-token", status_code=200)
async def request_anonymous_token(
    election_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a one-time anonymous vote token for an election.
    Required before voting in anonymous elections. One token per user per election.
    """
    setting_repo = ElectionSettingRepository(session)
    setting = await setting_repo.read_one(
        condition=ElectionSetting.election_id == election_id
    )
    if not setting or not setting.anonymous:
        raise HTTPException(
            status_code=400,
            detail="Election does not support anonymous voting",
        )

    token_repo = AnonymousVoteTokenRepository(session)
    existing = await token_repo.get_by_user_and_election(
        str(current_user.id), election_id
    )
    if existing:
        if existing.used_at and not setting.allow_revoting:
            raise HTTPException(
                status_code=400,
                detail="You have already voted in this election",
            )
        return JSONResponse(content={"token": existing.token})

    from app.models.anonymous_vote_token import AnonymousVoteToken
    from datetime import datetime, timezone

    token = secrets.token_urlsafe(32)
    token_record = AnonymousVoteToken(
        election_id=election_id,
        user_id=str(current_user.id),
        token=token,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    await token_repo.create(token_record)
    logger.info(f"Created anonymous token for user {current_user.id} election {election_id}")
    return JSONResponse(content={"token": token})


@router.post("", status_code=201)
async def create_vote(
    vote_data: VoteCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new vote.
    For anonymous elections, include anonymous_token from request-token endpoint.
    """
    logger.info(
        f"Creating vote for election {vote_data.election_id} by user {current_user.id}"
    )

    vote = await vote_service.create_vote(
        session=session,
        vote_data=vote_data,
        user_id=str(current_user.id),
    )

    logger.info(f"Vote created successfully: {vote.id}")

    return JSONResponse(
        content=vote.model_dump(mode="json"), status_code=201
    )


@router.post("/batch", status_code=201)
async def create_votes_batch(
    batch_data: VoteBatchCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create multiple votes at once (for max_votes > 1).
    For anonymous elections, include anonymous_token from request-token endpoint.
    """
    logger.info(
        f"Creating batch vote for election {batch_data.election_id} by user {current_user.id}"
    )

    votes = await vote_service.create_votes_batch(
        session=session,
        batch_data=batch_data,
        user_id=str(current_user.id),
    )

    return JSONResponse(
        content={"votes": [v.model_dump(mode="json") for v in votes]},
        status_code=201,
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
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get current user's vote for a specific election.
    For anonymous elections, returns { has_voted: true } without candidate info.
    """
    logger.info(
        f"Getting vote for election {election_id} by user {current_user.id}"
    )

    from app.repository.election_setting_repository import ElectionSettingRepository

    setting_repo = ElectionSettingRepository(session)
    setting = await setting_repo.read_one(
        condition=ElectionSetting.election_id == election_id
    )

    if setting and setting.anonymous:
        has_voted = await vote_service.has_user_voted_anonymous(
            session, election_id, str(current_user.id)
        )
        if not has_voted:
            from app.exceptions.user import VoteNotFoundError

            raise VoteNotFoundError(
                f"Vote for election {election_id} by user {current_user.id} not found"
            )
        return JSONResponse(content={"has_voted": True})

    vote = await vote_service.get_user_vote_for_election(
        election_id, str(current_user.id)
    )

    if not vote:
        from app.exceptions.user import VoteNotFoundError

        raise VoteNotFoundError(
            f"Vote for election {election_id} by user {current_user.id} not found"
        )

    return JSONResponse(content=vote.model_dump(mode="json"))
