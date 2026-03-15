from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ElectionSettingBase(BaseModel):
    """Base schema for ElectionSetting with common fields."""

    allow_revoting: bool = True
    max_votes: int = Field(
        default=1, ge=1, description="Maximum number of votes allowed"
    )
    require_auth: bool = True
    anonymous: bool = Field(
        default=False, description="Anonymous voting (votes stored with token instead of user id)"
    )


class ElectionSettingCreate(ElectionSettingBase):
    """Schema for creating a new election setting."""

    election_id: str


class ElectionSettingUpdate(BaseModel):
    """Schema for updating election setting."""

    allow_revoting: Optional[bool] = None
    max_votes: Optional[int] = Field(
        None, ge=1, description="Maximum number of votes allowed"
    )
    require_auth: Optional[bool] = None
    anonymous: Optional[bool] = None


class ElectionSettingResponse(ElectionSettingBase):
    """Schema for election setting response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    election_id: str

