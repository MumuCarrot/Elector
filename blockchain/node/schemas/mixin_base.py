from uuid import uuid4

from pydantic import BaseModel, Field


class MixinBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="The unique identifier of the mixin")