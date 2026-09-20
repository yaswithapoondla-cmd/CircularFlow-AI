"""
Phase 20: Email Service for CircularFlow AI
============================================

Sends institutional email notifications when a circular is officially published.

Provider: Resend (https://resend.com) — HTTP API, no SMTP required.
Fallback:  SMTP via Python smtplib if SMTP_HOST is configured instead.

Configuration (backend/.env):
    EMAIL_PROVIDER_API_KEY   – Resend API key  (e.g. re_xxxxxxxxxxxx)
    EMAIL_FROM               – Sender address  (e.g. noreply@vignan.ac.in)
    EMAIL_FROM_NAME          – Sender display name (e.g. CircularFlow AI)
    EMAIL_ENABLED            – Set to "false" to silence all emails (default: true)

    # SMTP fallback (only used when EMAIL_PROVIDER_API_KEY is absent)
    SMTP_HOST                – SMTP server hostname
    SMTP_PORT                – SMTP port (default: 587)
    SMTP_USER                – SMTP username
    SMTP_PASSWORD            – SMTP password
    SMTP_TLS                 – true/false (default: true)

SECURITY:
  - Credentials are read only from environment variables.
  - API keys are NEVER logged or returned in API responses.
  - If configuration is missing, emails are silently skipped and the
    circular publication continues uninterrupted.
"""
import os
import uuid
import logging
import smtplib
import json
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional

import urllib.request
import urllib.error

from sqlalchemy.orm import Session

from ..models.email_delivery_logs import EmailDeliveryLog
from ..models.audit_logs import AuditLog

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Configuration helpers (no secrets in logs)
# ─────────────────────────────────────────────────────────────────────────────

def _get_config() -> dict:
    return {
        "api_key": os.getenv("EMAIL_PROVIDER_API_KEY", ""),
        "from_addr": os.getenv("EMAIL_FROM", "noreply@vignan.ac.in"),
        "from_name": os.getenv("EMAIL_FROM_NAME", "CircularFlow AI — Vignan's University"),
        "enabled": os.getenv("EMAIL_ENABLED", "true").strip().lower() not in ("false", "0", "no"),
        "smtp_host": os.getenv("SMTP_HOST", ""),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": os.getenv("SMTP_USER", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "smtp_tls": os.getenv("SMTP_TLS", "true").strip().lower() not in ("false", "0", "no"),
        "frontend_url": os.getenv("FRONTEND_URL", "https://circularflow.vignan.ac.in"),
    }


def _is_configured(config: dict) -> bool:
    """Returns True if at least one delivery method is usable."""
    return bool(config["api_key"] or config["smtp_host"])


# ─────────────────────────────────────────────────────────────────────────────
# HTML email template
# ─────────────────────────────────────────────────────────────────────────────

def _build_html(
    *,
    title: str,
    ref_no: str,
    department: str,
    priority: str,
    effective_date: str,
    summary: str,
    published_by: str,
    frontend_url: str,
    requires_action: bool = False,
) -> str:
    priority_color = {
        "Critical": "#dc2626",
        "High":     "#ea580c",
        "Medium":   "#ca8a04",
        "Low":      "#16a34a",
    }.get(priority, "#6366f1")

    action_block = ""
    if requires_action:
        action_block = f"""
        <div style="background:#fef9c3;border:1px solid #fde047;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0;font-size:14px;color:#713f12;">
            <strong>⚠ Action Required:</strong> Please log in to CircularFlow AI, review this circular,
            and submit your digital acknowledgement before the effective date.
          </p>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Inter,Segoe UI,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08);">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#1e3a8a,#4f46e5);padding:28px 32px;">
            <p style="margin:0;color:#bfdbfe;font-size:11px;letter-spacing:.12em;text-transform:uppercase;font-weight:600;">
              Vignan's Foundation for Science, Technology &amp; Research
            </p>
            <h1 style="margin:6px 0 0;color:#ffffff;font-size:22px;font-weight:800;letter-spacing:-.02em;">
              CircularFlow AI
            </h1>
            <p style="margin:4px 0 0;color:#a5b4fc;font-size:12px;">Institutional Governance OS</p>
          </td>
        </tr>

        <!-- Badge -->
        <tr>
          <td style="padding:24px 32px 0;">
            <span style="display:inline-block;background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;
                         border-radius:6px;padding:4px 12px;font-size:11px;font-weight:700;letter-spacing:.08em;">
              NEW INSTITUTIONAL CIRCULAR
            </span>
          </td>
        </tr>

        <!-- Title -->
        <tr>
          <td style="padding:16px 32px 0;">
            <h2 style="margin:0;color:#0f172a;font-size:20px;font-weight:700;line-height:1.3;">
              {title}
            </h2>
          </td>
        </tr>

        <!-- Meta grid -->
        <tr>
          <td style="padding:20px 32px 0;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="50%" style="padding-bottom:12px;">
                  <p style="margin:0;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Reference No.</p>
                  <p style="margin:4px 0 0;font-size:14px;color:#1e293b;font-weight:700;font-family:monospace;">{ref_no}</p>
                </td>
                <td width="50%" style="padding-bottom:12px;">
                  <p style="margin:0;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Priority</p>
                  <p style="margin:4px 0 0;font-size:14px;font-weight:700;color:{priority_color};">{priority}</p>
                </td>
              </tr>
              <tr>
                <td width="50%" style="padding-bottom:12px;">
                  <p style="margin:0;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Department</p>
                  <p style="margin:4px 0 0;font-size:14px;color:#1e293b;font-weight:600;">{department}</p>
                </td>
                <td width="50%" style="padding-bottom:12px;">
                  <p style="margin:0;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Effective Date</p>
                  <p style="margin:4px 0 0;font-size:14px;color:#1e293b;font-weight:600;">{effective_date}</p>
                </td>
              </tr>
              <tr>
                <td colspan="2">
                  <p style="margin:0;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Published By</p>
                  <p style="margin:4px 0 0;font-size:14px;color:#1e293b;font-weight:600;">{published_by}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Divider -->
        <tr><td style="padding:16px 32px 0;"><hr style="border:none;border-top:1px solid #e2e8f0;margin:0;"></td></tr>

        <!-- Summary -->
        <tr>
          <td style="padding:20px 32px 0;">
            <p style="margin:0;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.06em;font-weight:600;">Summary</p>
            <p style="margin:8px 0 0;font-size:14px;color:#334155;line-height:1.6;">{summary}</p>
          </td>
        </tr>

        {action_block}

        <!-- CTA -->
        <tr>
          <td style="padding:24px 32px;">
            <a href="{frontend_url}/circulars"
               style="display:inline-block;background:linear-gradient(135deg,#4f46e5,#6366f1);color:#ffffff;
                      text-decoration:none;font-size:14px;font-weight:700;padding:12px 28px;
                      border-radius:8px;letter-spacing:.02em;">
              View in CircularFlow AI →
            </a>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f8fafc;padding:20px 32px;border-top:1px solid #e2e8f0;">
            <p style="margin:0;font-size:11px;color:#94a3b8;line-height:1.6;">
              This is an automated notification from <strong>CircularFlow AI</strong>, the institutional
              governance platform of Vignan's Foundation for Science, Technology &amp; Research.<br>
              Please do not reply to this email. For queries, contact your department administrator.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _build_plain(
    *,
    title: str,
    ref_no: str,
    department: str,
    priority: str,
    effective_date: str,
    summary: str,
    published_by: str,
    frontend_url: str,
    requires_action: bool = False,
) -> str:
    action_note = (
        "\n⚠ ACTION REQUIRED: Log in and acknowledge this circular before the effective date.\n"
        if requires_action else ""
    )
    return f"""CircularFlow AI — Institutional Governance OS
Vignan's Foundation for Science, Technology & Research
══════════════════════════════════════════════════════

NEW INSTITUTIONAL CIRCULAR

Title:          {title}
Reference No.:  {ref_no}
Department:     {department}
Priority:       {priority}
Effective Date: {effective_date}
Published By:   {published_by}
{action_note}
Summary:
{summary}

View in CircularFlow AI:
{frontend_url}/circulars

──────────────────────────────────────────────────────
This is an automated notification. Do not reply.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Low-level delivery functions
# ─────────────────────────────────────────────────────────────────────────────

def _send_via_resend(
    *,
    api_key: str,
    from_addr: str,
    from_name: str,
    to_email: str,
    to_name: str,
    subject: str,
    html: str,
    plain: str,
    pdf_bytes: Optional[bytes] = None,
    pdf_filename: Optional[str] = None,
) -> None:
    """Send using Resend REST API (no extra library needed — pure urllib)."""
    attachments = []
    if pdf_bytes and pdf_filename:
        import base64
        attachments = [{
            "filename": pdf_filename,
            "content": base64.b64encode(pdf_bytes).decode("ascii"),
        }]

    payload: dict = {
        "from": f"{from_name} <{from_addr}>",
        "to": [f"{to_name} <{to_email}>" if to_name else to_email],
        "subject": subject,
        "html": html,
        "text": plain,
    }
    if attachments:
        payload["attachments"] = attachments

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.status not in (200, 201):
            body = resp.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Resend API returned HTTP {resp.status}: {body[:200]}")


def _send_via_smtp(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    smtp_tls: bool,
    from_addr: str,
    from_name: str,
    to_email: str,
    to_name: str,
    subject: str,
    html: str,
    plain: str,
    pdf_bytes: Optional[bytes] = None,
    pdf_filename: Optional[str] = None,
) -> None:
    """Send using Python smtplib (SMTP/STARTTLS fallback)."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = f"{to_name} <{to_email}>" if to_name else to_email

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    if pdf_bytes and pdf_filename:
        attachment = MIMEBase("application", "pdf")
        attachment.set_payload(pdf_bytes)
        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", "attachment", filename=pdf_filename)
        msg.attach(attachment)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
        if smtp_tls:
            server.starttls()
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
        server.sendmail(from_addr, [to_email], msg.as_string())


# ─────────────────────────────────────────────────────────────────────────────
# Main public API
# ─────────────────────────────────────────────────────────────────────────────

def send_single_notification(
    *,
    to_email: str,
    to_name: str,
    subject: str,
    title: str,
    ref_no: str,
    department: str,
    priority: str,
    effective_date: str,
    summary: str,
    published_by: str,
    requires_action: bool = False,
    pdf_bytes: Optional[bytes] = None,
    pdf_filename: Optional[str] = None,
) -> None:
    """
    Attempt to send one notification email.
    Raises on failure so the caller can record FAILED status.
    """
    config = _get_config()
    if not config["enabled"]:
        logger.info("[EmailService] Email notifications disabled (EMAIL_ENABLED=false). Skipping.")
        return
    if not _is_configured(config):
        logger.info(
            "[EmailService] No email provider configured "
            "(set EMAIL_PROVIDER_API_KEY or SMTP_HOST). Skipping."
        )
        return

    html = _build_html(
        title=title, ref_no=ref_no, department=department, priority=priority,
        effective_date=effective_date, summary=summary, published_by=published_by,
        frontend_url=config["frontend_url"], requires_action=requires_action,
    )
    plain = _build_plain(
        title=title, ref_no=ref_no, department=department, priority=priority,
        effective_date=effective_date, summary=summary, published_by=published_by,
        frontend_url=config["frontend_url"], requires_action=requires_action,
    )

    if config["api_key"]:
        _send_via_resend(
            api_key=config["api_key"],
            from_addr=config["from_addr"],
            from_name=config["from_name"],
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html=html,
            plain=plain,
            pdf_bytes=pdf_bytes,
            pdf_filename=pdf_filename,
        )
    else:
        _send_via_smtp(
            smtp_host=config["smtp_host"],
            smtp_port=config["smtp_port"],
            smtp_user=config["smtp_user"],
            smtp_password=config["smtp_password"],
            smtp_tls=config["smtp_tls"],
            from_addr=config["from_addr"],
            from_name=config["from_name"],
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html=html,
            plain=plain,
            pdf_bytes=pdf_bytes,
            pdf_filename=pdf_filename,
        )


def dispatch_circular_notifications(
    *,
    db: Session,
    circular_id: str,
    circular_ref: str,
    title: str,
    department: str,
    priority: str,
    effective_date: str,
    summary: str,
    published_by: str,
    published_by_email: Optional[str],
    target_audience: List[str],
    requires_action: bool = False,
    pdf_bytes: Optional[bytes] = None,
    pdf_filename: Optional[str] = None,
) -> dict:
    """
    Determine recipients and send notification emails for a published circular.

    Recipient selection logic:
    1. Query `recipients` table whose department matches the circular's department.
    2. Also include all `users` whose role is Registrar (institutional admin) OR whose
       department_name matches — so governance leads are always notified.
    3. Exclude the publisher (published_by_email) to avoid duplicating their own notification
       unless they are in the audience by another rule.
    4. Deduplicate by email address.

    This runs in a background task — errors are recorded, not raised to the HTTP layer.
    Returns a summary dict: {"sent": N, "failed": M, "skipped": K}
    """
    from ..models.recipients import Recipient
    from ..models.users import User
    from sqlalchemy import or_, func

    config = _get_config()
    if not config["enabled"]:
        logger.info("[EmailService] Email notifications disabled. dispatch skipped.")
        _write_audit(db, circular_id, circular_ref, sent=0, failed=0, skipped=0,
                     reason="EMAIL_ENABLED=false")
        return {"sent": 0, "failed": 0, "skipped": 0}

    if not _is_configured(config):
        logger.info("[EmailService] Email not configured. dispatch skipped.")
        _write_audit(db, circular_id, circular_ref, sent=0, failed=0, skipped=0,
                     reason="no provider configured")
        return {"sent": 0, "failed": 0, "skipped": 0}

    # ── Build recipient list ──────────────────────────────────────────────────
    email_map: dict[str, str] = {}  # email → name

    # 1. Dept-matched recipients from `recipients` table
    dept_recipients = db.query(Recipient).filter(
        func.lower(Recipient.department) == department.lower()
    ).all()
    for r in dept_recipients:
        if r.email:
            email_map[r.email.lower()] = r.name or ""

    # 2. If audience contains "all" or "all staff" → add every user
    audience_lower = [a.lower() for a in target_audience]
    include_all = any(kw in " ".join(audience_lower) for kw in ("all staff", "all users", "entire university"))

    # 3. Registrar / Admin users always receive institutional circulars
    user_query = db.query(User).filter(
        or_(
            func.lower(User.role) == "registrar",
            func.lower(User.department_name) == department.lower(),
            *([sa_true()] if include_all else []),
        )
    )
    for u in user_query.all():
        if u.email:
            email_map[u.email.lower()] = u.name or ""

    # 4. Remove publisher to avoid self-notification
    if published_by_email:
        email_map.pop(published_by_email.lower(), None)

    sent = failed = skipped = 0
    subject = f"[New Circular] {title} ({circular_ref})"

    for email, name in email_map.items():
        log_id = str(uuid.uuid4())
        log_entry = EmailDeliveryLog(
            id=log_id,
            circular_id=circular_id,
            circular_ref=circular_ref,
            recipient_email=email,
            recipient_name=name,
            status="PENDING",
            created_at=datetime.now(timezone.utc),
        )
        db.add(log_entry)
        db.flush()  # get the row into DB before attempt

        try:
            send_single_notification(
                to_email=email,
                to_name=name,
                subject=subject,
                title=title,
                ref_no=circular_ref,
                department=department,
                priority=priority,
                effective_date=effective_date,
                summary=summary,
                published_by=published_by,
                requires_action=requires_action,
                pdf_bytes=pdf_bytes,
                pdf_filename=pdf_filename,
            )
            log_entry.status = "SENT"
            log_entry.sent_at = datetime.now(timezone.utc)
            sent += 1
            logger.info("[EmailService] Sent to %s for circular %s", email, circular_ref)
        except Exception as exc:  # noqa: BLE001
            log_entry.status = "FAILED"
            # Store error without leaking credential details
            safe_err = str(exc)
            if any(secret in safe_err for secret in (
                config.get("api_key", ""), config.get("smtp_password", "")
            )):
                safe_err = "[error details redacted — check server logs]"
            log_entry.error_message = safe_err[:1000]
            failed += 1
            logger.error("[EmailService] Failed to send to %s: %s", email,
                         "[error redacted]" if "api_key" in safe_err else safe_err)

        db.commit()

    _write_audit(db, circular_id, circular_ref, sent=sent, failed=failed, skipped=skipped)
    logger.info(
        "[EmailService] Dispatch complete for %s — sent=%d failed=%d skipped=%d",
        circular_ref, sent, failed, skipped,
    )
    return {"sent": sent, "failed": failed, "skipped": skipped}


def _write_audit(
    db: Session,
    circular_id: str,
    circular_ref: str,
    *,
    sent: int,
    failed: int,
    skipped: int,
    reason: str = "",
) -> None:
    """Record EMAIL_NOTIFICATION_SENT / EMAIL_NOTIFICATION_FAILED in audit_logs."""
    try:
        event_type = "EMAIL_NOTIFICATION_SENT" if failed == 0 else "EMAIL_NOTIFICATION_FAILED"
        description = (
            f"Email notifications for {circular_ref}: "
            f"{sent} sent, {failed} failed, {skipped} skipped."
        )
        if reason:
            description += f" Reason: {reason}"

        log = AuditLog(
            id=str(uuid.uuid4()),
            event_type=event_type,
            description=description,
            related_circular_id=circular_id,
            event_metadata={
                "circular_ref": circular_ref,
                "sent": sent,
                "failed": failed,
                "skipped": skipped,
            },
        )
        db.add(log)
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.error("[EmailService] Failed to write audit log: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience import alias used in dispatch_circular_notifications
# ─────────────────────────────────────────────────────────────────────────────
def sa_true():
    """Return an always-true SQLAlchemy clause (for include_all branch)."""
    from sqlalchemy import true
    return true()
