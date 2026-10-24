from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    sender_id: int | None = None
    recipient_phone: str = Field(..., min_length=7, max_length=20)
    amount: float = Field(..., gt=0)


class TransactionRead(BaseModel):
    id: int
    sender_id: int
    recipient_phone: str
    amount: float
    status: str
