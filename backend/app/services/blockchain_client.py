from datetime import datetime, timezone

import httpx

from app.core.logging_config import get_logger
from app.core.settings import settings
from app.exceptions.user import BlockchainConnectionError

logger = get_logger("blockchain_client")

TRANSACTIONS_NEW_PATH = "/blockchain/transactions/new"


def _get_blockchain_base_url() -> str:
    """Build blockchain node base URL from settings."""

    host = settings.blockchain_settings.BLOCKCHAIN_HOST.rstrip("/")
    port = settings.blockchain_settings.BLOCKCHAIN_PORT
    return f"{host}:{port}"


async def create_transaction(
    election_id: str,
    voter_id: str,
    candidate_id: str | None = None,
    created_at: datetime | None = None,
) -> dict:
    """Send a new transaction to the blockchain node."""
    
    base_url = _get_blockchain_base_url()
    url = f"{base_url}{TRANSACTIONS_NEW_PATH}"

    timestamp = created_at or datetime.now(timezone.utc)

    payload = {
        "election_id": election_id,
        "voter_id": voter_id,
        "candidate_id": candidate_id if candidate_id else None,
        "created_at": timestamp.isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(
                "Transaction sent to blockchain: transaction_id=%s election_id=%s voter_id=%s candidate_id=%s created_at=%s",
                result["transaction_id"],
                result["election_id"],
                result["voter_id"],
                result["candidate_id"],
                result["created_at"],
            )
            return result

    except httpx.ConnectError as e:
        logger.error("Blockchain connection failed: %s", e)
        raise BlockchainConnectionError(
            detail=f"Could not connect to blockchain node at {base_url}"
        ) from e

    except httpx.HTTPStatusError as e:
        logger.error("Blockchain API error: %s - %s", e.response.status_code, e.response.text)
        raise BlockchainConnectionError(
            detail=f"Blockchain node returned error: {e.response.status_code}"
        ) from e


async def _get_json(url: str) -> dict:
    """GET request to blockchain API."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError as e:
        logger.error("Blockchain connection failed: %s", e)
        raise BlockchainConnectionError(
            detail=f"Could not connect to blockchain node at {url}"
        ) from e
    except httpx.HTTPStatusError as e:
        logger.error("Blockchain API error: %s - %s", e.response.status_code, e.response.text)
        raise BlockchainConnectionError(
            detail=f"Blockchain node returned error: {e.response.status_code}"
        ) from e


async def get_votes_by_election(election_id: str) -> dict:
    """Get all votes for a specific election (DB query by election_id)."""

    base_url = _get_blockchain_base_url()
    url = f"{base_url}/api/elid/{election_id}"
    return await _get_json(url)


async def get_votes_by_user(user_id: str) -> list[dict]:
    """Get all votes by a specific user (DB query by voter_id)."""

    base_url = _get_blockchain_base_url()
    url = f"{base_url}/api/uid/{user_id}"
    data = await _get_json(url)
    return data.get("votes", [])


async def get_user_vote_for_election(
    election_id: str, user_id: str
) -> dict | None:
    """Get user's vote for a specific election (DB query by election_id + voter_id)."""

    base_url = _get_blockchain_base_url()
    url = f"{base_url}/api/elid/{election_id}/uid/{user_id}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
            
    except httpx.ConnectError as e:
        logger.error("Blockchain connection failed: %s", e)
        raise BlockchainConnectionError(
            detail=f"Could not connect to blockchain node at {base_url}"
        ) from e

    except httpx.HTTPStatusError as e:
        logger.error("Blockchain API error: %s - %s", e.response.status_code, e.response.text)
        raise BlockchainConnectionError(
            detail=f"Blockchain node returned error: {e.response.status_code}"
        ) from e