from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CandidateBase(BaseModel):
    """Base schema for Candidate with common fields."""

    name: str = Field(..., min_length=1, description="Candidate name")
    description: Optional[str] = None


class CandidateCreate(CandidateBase):
    """Schema for creating a new candidate."""

    pass


class CandidateUpdate(BaseModel):
    """Schema for updating candidate."""

    name: Optional[str] = Field(
        None, min_length=1, description="Candidate name"
    )
    description: Optional[str] = None


class CandidateResponse(CandidateBase):
    """Schema for candidate response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    election_id: str

