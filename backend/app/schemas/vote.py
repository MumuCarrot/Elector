from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VoteBase(BaseModel):
    """Base schema for Vote with common fields."""

    election_id: str
    voter_id: str
    candidate_id: str | None = None


class VoteCreate(BaseModel):
    """Schema for creating a new vote."""

    election_id: str
    candidate_id: str | None = None
    anonymous_token: str | None = Field(
        None,
        description="One-time token for anonymous voting (required when election is anonymous)",
    )


class VoteBatchCreate(BaseModel):
    """Schema for creating multiple votes at once (e.g. when max_votes > 1)."""

    election_id: str
    candidate_ids: list[str] = Field(..., min_length=1)
    anonymous_token: str | None = Field(
        None,
        description="One-time token for anonymous voting (required when election is anonymous)",
    )


class VoteUpdate(BaseModel):
    """Schema for updating vote."""

    election_id: Optional[str] = None
    voter_id: Optional[str] = None
    candidate_id: Optional[str | None] = None


class VoteResponse(VoteBase):
    """Schema for vote response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: Optional[datetime] = None

