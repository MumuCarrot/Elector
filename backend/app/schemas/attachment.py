from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AttachmentBase(BaseModel):
    """Base schema for Attachment with common fields."""
    file_url: str = Field(..., min_length=1, description="URL of the attached file")
    
    @field_validator("file_url")
    @classmethod
    def validate_pdf_file(cls, v: str) -> str:
        """Validate that the file URL points to a PDF file."""
        if not v.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are allowed")
        return v


class AttachmentCreate(AttachmentBase):
    """Schema for creating a new attachment."""
    user_id: Optional[str] = None
    election_id: Optional[str] = None
    candidate_id: Optional[str] = None


class AttachmentUpdate(BaseModel):
    """Schema for updating attachment."""
    file_url: Optional[str] = Field(None, min_length=1, description="URL of the attached file")
    user_id: Optional[str] = None
    election_id: Optional[str] = None
    candidate_id: Optional[str] = None


class AttachmentResponse(AttachmentBase):
    """Schema for attachment response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    election_id: Optional[str] = None
    candidate_id: Optional[str] = None
    uploaded_at: Optional[datetime] = None