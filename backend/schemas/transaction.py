from pydantic import BaseModel


class TransactionCreate(BaseModel):
    sender_id: int
    recipient_phone: str
    amount: float