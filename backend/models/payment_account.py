from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class PaymentAccount(Base):
    __tablename__ = "payment_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)

    # NEW: the phone number linked to this account. Not unique on purpose:
    # two accounts can share a phone number (a SHARED_PHONE relationship).
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20), index=True, nullable=True
    )
