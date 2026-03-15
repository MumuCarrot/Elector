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
    candidate_id: str,
    created_at: datetime | None = None,
) -> dict:
    """Send a new transaction to the blockchain node."""
    
    base_url = _get_blockchain_base_url()
    url = f"{base_url}{TRANSACTIONS_NEW_PATH}"

    timestamp = created_at or datetime.now(timezone.utc)

    payload = {
        "election_id": election_id,
        "voter_id": voter_id,
        "candidate_id": candidate_id,
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
