"""
Phase 20: Circular Publication & Email Notification Endpoints
─────────────────────────────────────────────────────────────
POST /api/v1/circulars/{circular_id}/publish
    Marks a circular status as "Active" (published) and triggers
    background email dispatch to recipients.

GET  /api/v1/circulars/{circular_id}/notification-status
    Returns the email delivery summary for a published circular.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...auth.deps import get_current_user
from ...models.users import User
from ...models.circulars import Circular
from ...models.email_delivery_logs import EmailDeliveryLog
from ...models.audit_logs import AuditLog
from ...services.email_service import dispatch_circular_notifications

router = APIRouter(
    prefix="/circulars",
    tags=["Circular Publication & Notifications"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class PublishRequest(BaseModel):
    """Optional overrides for the publish action."""
    published_by: Optional[str] = Field(None, description="Display name of the authorising user")
    published_by_email: Optional[str] = Field(None, description="Email of the authorising user (excluded from recipient list)")
    send_email_notifications: bool = Field(True, description="Set false to suppress emails for this publish")


class PublishResponse(BaseModel):
    circular_id: str
    ref_no: str
    status: str
    published_at: str
    email_notifications_queued: bool
    message: str


class NotificationStatusResponse(BaseModel):
    circular_id: str
    ref_no: str
    total: int
    sent: int
    failed: int
    pending: int
    logs: list


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/circulars/{circular_id}/publish
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/{circular_id}/publish",
    response_model=PublishResponse,
    summary="Publish a Circular",
    description=(
        "Marks a DRAFT circular as Active (Published) and dispatches email notifications "
        "to matching recipients in the background. The HTTP response is immediate — "
        "email delivery happens asynchronously and does not block the response."
    ),
    status_code=status.HTTP_200_OK,
)
async def publish_circular(
    circular_id: str,
    body: Optional[PublishRequest] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PublishResponse:
    """
    Authenticated endpoint.  Publishes the circular and queues email delivery.
    Only circulars in Draft / Under Review status can be published.
    """
    # ── 1. Resolve circular ──────────────────────────────────────────────────
    from sqlalchemy import or_, func
    circular = db.query(Circular).filter(
        or_(
            func.lower(Circular.id) == circular_id.strip().lower(),
            func.lower(Circular.ref_no) == circular_id.strip().lower(),
        )
    ).first()

    if not circular:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Circular '{circular_id}' not found.",
        )

    # ── 2. Guard: don't re-publish ────────────────────────────────────────────
    if circular.status.lower() == "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Circular '{circular.ref_no}' is already published (status: Active).",
        )

    # ── 3. Determine publisher identity ───────────────────────────────────────
    req = body or PublishRequest()
    publisher_name = req.published_by or current_user.name or "Registrar"
    publisher_email = req.published_by_email or current_user.email or None

    # ── 4. Update circular status ─────────────────────────────────────────────
    circular.status = "Active"
    circular.updated_at = datetime.now(timezone.utc)
    published_at_iso = datetime.now(timezone.utc).isoformat()

    # ── 5. Write audit log ────────────────────────────────────────────────────
    audit = AuditLog(
        id=str(uuid.uuid4()),
        event_type="CIRCULAR_PUBLISHED",
        description=f"Circular {circular.ref_no} published by {publisher_name}.",
        user_name=publisher_name,
        user_role=current_user.role,
        related_circular_id=circular.id,
        event_metadata={
            "ref_no": circular.ref_no,
            "title": circular.title,
            "department": circular.department,
            "priority": circular.priority,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(circular)

    # ── 6. Queue email dispatch ───────────────────────────────────────────────
    notifications_queued = False
    if req.send_email_notifications:
        background_tasks.add_task(
            dispatch_circular_notifications,
            db=db,
            circular_id=circular.id,
            circular_ref=circular.ref_no,
            title=circular.title,
            department=circular.department,
            priority=circular.priority,
            effective_date=circular.effective_date,
            summary=circular.summary,
            published_by=publisher_name,
            published_by_email=publisher_email,
            target_audience=circular.target_audience or [],
            requires_action=bool(circular.required_actions),
        )
        notifications_queued = True

    return PublishResponse(
        circular_id=circular.id,
        ref_no=circular.ref_no,
        status=circular.status,
        published_at=published_at_iso,
        email_notifications_queued=notifications_queued,
        message=(
            f"Circular '{circular.ref_no}' published successfully. "
            + ("Email notifications queued for delivery." if notifications_queued
               else "Email notifications suppressed by request.")
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/circulars/{circular_id}/notification-status
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{circular_id}/notification-status",
    response_model=NotificationStatusResponse,
    summary="Email Notification Delivery Status",
    description="Returns a summary of email delivery statuses for a published circular.",
)
async def get_notification_status(
    circular_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationStatusResponse:
    """Authenticated: fetch delivery status for all notification attempts on a circular."""
    # Resolve circular
    from sqlalchemy import or_, func
    circular = db.query(Circular).filter(
        or_(
            func.lower(Circular.id) == circular_id.strip().lower(),
            func.lower(Circular.ref_no) == circular_id.strip().lower(),
        )
    ).first()
    if not circular:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Circular '{circular_id}' not found.",
        )

    logs = (
        db.query(EmailDeliveryLog)
        .filter(EmailDeliveryLog.circular_id == circular.id)
        .order_by(EmailDeliveryLog.created_at.desc())
        .all()
    )

    sent = sum(1 for l in logs if l.status == "SENT")
    failed = sum(1 for l in logs if l.status == "FAILED")
    pending = sum(1 for l in logs if l.status == "PENDING")

    log_data = [
        {
            "id": l.id,
            "recipient_email": l.recipient_email,
            "recipient_name": l.recipient_name,
            "status": l.status,
            "sent_at": l.sent_at.isoformat() if l.sent_at else None,
            "error_message": l.error_message,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]

    return NotificationStatusResponse(
        circular_id=circular.id,
        ref_no=circular.ref_no,
        total=len(logs),
        sent=sent,
        failed=failed,
        pending=pending,
        logs=log_data,
    )
