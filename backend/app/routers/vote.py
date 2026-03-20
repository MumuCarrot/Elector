import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.dependencies.database import get_db
from app.dependencies.token import get_current_user
from app.models.anonymous_vote_token import AnonymousVoteToken
from app.models.election_setting import ElectionSetting
from app.models.user import User
from app.repository.anonymous_vote_token_repository import AnonymousVoteTokenRepository
from app.repository.election_setting_repository import ElectionSettingRepository
from app.schemas.vote import VoteBatchCreate, VoteCreate
from app.services.vote import vote_service

router = APIRouter(tags=["votes"])
logger = get_logger("vote_router")


@router.post("/election/{election_id}/request-token", status_code=200)
async def request_anonymous_token(
    election_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Issues or returns an existing anonymous voting token for this user+election.

    Args:
        election_id: Target election.
        current_user: Authenticated user (real identity stored server-side only).
        session: DB session.

    Returns:
        JSONResponse: ``{"token": "..."}``.

    Raises:
        HTTPException: 400 if election is not anonymous or user already voted
            without revote allowed.

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

    token = secrets.token_urlsafe(32)
    token_record = AnonymousVoteToken(
        election_id=election_id,
        user_id=str(current_user.id),
        token=token,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    await token_repo.create(token_record)
    logger.info(
        "Created anonymous token for user %s election %s",
        current_user.id,
        election_id,
    )
    return JSONResponse(content={"token": token})


@router.post("", status_code=201)
async def create_vote(
    vote_data: VoteCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Submits a single vote to the blockchain (authenticated user).

    Args:
        vote_data: Election, candidate, optional ``anonymous_token``.
        current_user: Caller.
        session: DB session.

    Returns:
        JSONResponse: 201 with vote echo from chain.

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
    """Submits multiple votes in one request (e.g. multi-select elections).

    Args:
        batch_data: Election, candidate id list, optional anonymous token.
        current_user: Caller.
        session: DB session.

    Returns:
        JSONResponse: 201 with ``votes`` array.

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
    """Lists on-chain votes for a user id (self-only).

    Args:
        user_id: Must equal ``current_user.id``.
        current_user: Authenticated user.

    Returns:
        JSONResponse: ``votes`` list (may be empty).

    Raises:
        HTTPException: 403 if ``user_id`` does not match caller.

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
    """Returns candidate -> vote count map from the blockchain read API.

    Args:
        election_id: Election id path parameter.

    Returns:
        JSONResponse: Mapping of candidate id strings to integer counts.

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
    """Returns the caller's vote for an election; anonymous mode hides candidate.

    Args:
        election_id: Election id.
        current_user: Authenticated user.
        session: DB session for anonymous flag lookup.

    Returns:
        JSONResponse: Vote payload or ``{"has_voted": true}`` for anonymous.

    Raises:
        VoteNotFoundError: No vote on record.

    """
    logger.info(
        f"Getting vote for election {election_id} by user {current_user.id}"
    )

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
