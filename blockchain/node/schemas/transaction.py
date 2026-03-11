from datetime import datetime

from pydantic import Field
from node.schemas.mixin_base import MixinBase


class Transaction(MixinBase):
    election_id: str = Field(..., description="The election identifier")
    voter_id: str = Field(..., description="The voter identifier")
    candidate_id: str = Field(..., description="The candidate identifier")
    created_at: datetime | None = Field(
        default=None,
        description="The timestamp when the vote was created",
    )