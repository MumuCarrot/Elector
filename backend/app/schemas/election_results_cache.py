from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ElectionResultsCacheBase(BaseModel):
    """Base schema for ElectionResultsCache with common fields."""

    results_json: Optional[str] = None


class ElectionResultsCacheCreate(ElectionResultsCacheBase):
    """Schema for creating a new election results cache."""

    election_id: str


class ElectionResultsCacheUpdate(BaseModel):
    """Schema for updating election results cache."""

    results_json: Optional[str] = None


class ElectionResultsCacheResponse(ElectionResultsCacheBase):
    """Schema for election results cache response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    election_id: str
    updated_at: Optional[datetime] = None

