from pydantic import BaseModel, Field


class BlockCandidate(BaseModel):
    """Minimal block data used in some hashing paths.

    Attributes:
        prev_hash: Previous block hash.
        txs: Raw transaction dicts.
        nonce: Proof-of-work nonce.

    """

    prev_hash: str = Field(..., description="The hash of the previous block")
    txs: list[dict] = Field(..., description="A list of transactions included in the block")
    nonce: int = Field(..., description="The nonce value for the block")
