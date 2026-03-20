from datetime import datetime

from pydantic import Field

from node.schemas.mixin_base import MixinBase


class Transaction(MixinBase):
    """Represents one vote: election, voter, optional candidate, and timestamp.

    Attributes:
        election_id: Election this vote belongs to.
        voter_id: User who cast the vote.
        candidate_id: Selected candidate, if applicable.
        created_at: When the vote was recorded in the application.

    """

    election_id: str = Field(..., description="The election identifier")
    voter_id: str = Field(..., description="The voter identifier")
    candidate_id: str | None = Field(
        default=None,
        description="The candidate identifier",
    )
    created_at: datetime | None = Field(
        default=None,
        description="The timestamp when the vote was created",
    )
