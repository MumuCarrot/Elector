from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.candidate import CandidateCreate, CandidateResponse
from app.schemas.election_setting import (
    ElectionSettingBase,
    ElectionSettingResponse,
)
from app.schemas.attachment import AttachmentCreate, AttachmentResponse


class ElectionBase(BaseModel):
    """Base schema for Election with common fields."""

    title: str = Field(..., min_length=1, description="Election title")
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    is_public: bool = True


class ElectionCreate(ElectionBase):
    """Schema for creating a new election."""

    candidates: List[CandidateCreate] = Field(
        ..., min_length=2, description="List of candidates for the election"
    )
    settings: Optional[ElectionSettingBase] = Field(
        None, description="Election settings"
    )
    attachments: Optional[List[AttachmentCreate]] = Field(
        None, description="List of PDF file attachments for the election"
    )


class ElectionUpdate(BaseModel):
    """Schema for updating election."""

    title: Optional[str] = Field(
        None, min_length=1, description="Election title"
    )
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_public: Optional[bool] = None
    candidates: Optional[List[CandidateCreate]] = Field(
        None, min_length=2, description="List of candidates for the election"
    )
    settings: Optional[ElectionSettingBase] = Field(
        None, description="Election settings"
    )
    attachments: Optional[List[AttachmentCreate]] = Field(
        None, description="List of PDF file attachments for the election"
    )


class ElectionResponse(ElectionBase):
    """Schema for election response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: Optional[str] = None
    created_at: Optional[datetime] = None
    candidates: List[CandidateResponse] = []
    settings: Optional[ElectionSettingResponse] = None
    attachments: List[AttachmentResponse] = []

