from pydantic import BaseModel, Field

from node.schemas.block import Block

class GossipChainRequestSchema(BaseModel):
    chain: list[Block] = Field(...)
    tx_ids: list[str] = Field(...)