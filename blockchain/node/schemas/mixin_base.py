from uuid import uuid4

from pydantic import BaseModel, Field


class MixinBase(BaseModel):
    """Shared base with UUID string primary key for API models.

    Attributes:
        id: Unique identifier; generated if omitted.

    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="The unique identifier of the mixin")
