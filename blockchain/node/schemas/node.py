from pydantic import BaseModel, ConfigDict, Field

class TransactionNewRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sender: str = Field(..., description="The address of the sender")
    recipient: str = Field(..., description="The address of the recipient")
    amount: float = Field(..., description="The amount to be transferred")


class RegisterNodeRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nodes: list[str] = Field(..., description="A list of node addresses to register")