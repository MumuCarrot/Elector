from pydantic import BaseModel, Field

from node.schemas.block import Block


class GossipChainRequestSchema(BaseModel):
    """Full chain snapshot plus transaction ids for mempool cleanup.

    Attributes:
        chain: Proposed longer valid chain from a peer.
        tx_ids: All transaction ids contained in ``chain`` (for mempool eviction).

    """

    chain: list[Block] = Field(...)
    tx_ids: list[str] = Field(...)
