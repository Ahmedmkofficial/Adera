from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class RelationshipType:
    """Allowed values for account_relationships.relationship_type.

    Plain strings (not a database enum), matching how the rest of this project
    stores statuses.
    """

    SHARED_PHONE = "SHARED_PHONE"
    SHARED_DEVICE = "SHARED_DEVICE"
    TRANSACTION = "TRANSACTION"
    RELATED_ACCOUNT = "RELATED_ACCOUNT"


class AccountRelationship(Base):
    """One connection (edge) between two payment accounts."""

    __tablename__ = "account_relationships"
    __table_args__ = (
        UniqueConstraint(
            "source_account_id",
            "target_account_id",
            "relationship_type",
            name="uq_account_relationships_edge",
        ),
        CheckConstraint("source_account_id <> target_account_id", name="no_self_loop"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_account_id: Mapped[int] = mapped_column(
        ForeignKey("payment_accounts.id"), index=True, nullable=False
    )
    target_account_id: Mapped[int] = mapped_column(
        ForeignKey("payment_accounts.id"), index=True, nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )
