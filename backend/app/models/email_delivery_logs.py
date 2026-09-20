"""
Phase 20: Email Notification Database Model
Table: email_delivery_logs

Tracks every email notification attempt for circular publications.
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Index
from ..db.base import Base


class EmailDeliveryLog(Base):
    """
    Records the delivery status of every email notification triggered
    by a circular publication event.  Delivery failures do NOT block
    the publish operation — the circular remains published regardless.
    """
    __tablename__ = "email_delivery_logs"

    id = Column(String(50), primary_key=True, index=True)
    circular_id = Column(String(50), nullable=False, index=True)
    circular_ref = Column(String(50), nullable=True)
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_name = Column(String(150), nullable=True)
    recipient_user_id = Column(String(50), nullable=True, index=True)  # FK-less for resilience
    # PENDING → SENT or FAILED
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_email_delivery_logs_circular_status", "circular_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<EmailDeliveryLog circular={self.circular_id} "
            f"recipient={self.recipient_email} status={self.status}>"
        )
