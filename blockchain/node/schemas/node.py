from pydantic import BaseModel, ConfigDict, Field


class TransactionNewRequest(BaseModel):
    """Example transfer-style payload (not used by current vote flow).

    Attributes:
        sender: Sender address or id.
        recipient: Recipient address or id.
        amount: Transfer amount.

    """

    model_config = ConfigDict(from_attributes=True)

    sender: str = Field(..., description="The address of the sender")
    recipient: str = Field(..., description="The address of the recipient")
    amount: float = Field(..., description="The amount to be transferred")


class RegisterNodeRequest(BaseModel):
    """Bulk-register peer node addresses ``host:port``.

    Attributes:
        nodes: List of ``host:port`` strings to add to the local peer set.

    """

    model_config = ConfigDict(from_attributes=True)

    nodes: list[str] = Field(..., description="A list of node addresses to register")
