from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class VoteBase(BaseModel):
    """Base schema for Vote with common fields."""

    election_id: str
    voter_id: str
    candidate_id: str | None = None


class VoteCreate(BaseModel):
    """Schema for creating a new vote."""

    election_id: str
    candidate_id: str | None = None


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

