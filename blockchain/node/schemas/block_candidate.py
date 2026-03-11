from pydantic import BaseModel, Field


class BlockCandidate(BaseModel):
    prev_hash: str = Field(..., description="The hash of the previous block")
    txs: list[dict] = Field(..., description="A list of transactions included in the block")
    nonce: int = Field(..., description="The nonce value for the block")