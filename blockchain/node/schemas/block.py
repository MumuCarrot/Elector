from pydantic import BaseModel, Field
from node.schemas.transaction import Transaction


class Block(BaseModel):
    index: int = Field(..., description="The index of the block in the blockchain")
    timestamp: float = Field(..., description="The timestamp when the block was created")
    transactions: list[Transaction] = Field(..., description="A list of transactions included in the block")
    nonce: int = Field(..., description="The nonce value for the block")
    previous_hash: str = Field(..., description="The hash of the previous block")

    def __repr__(self):
        return f"Block(index={self.index}')"