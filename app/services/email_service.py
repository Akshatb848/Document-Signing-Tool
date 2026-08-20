"""Optional SMTP email notifications."""

from __future__ import annotations

import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import Settings

IST = timezone(timedelta(hours=5, minutes=30))


def _format_timestamp() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def send_partner_notification(
    settings: Settings,
    *,
    partner_name: str,
    partner_email: str,
    document_filename: str,
    operator_name: str,
    log_id: str,
    cc_operator: bool = True,
) -> str:
    if not settings.email_enabled:
        return "skipped (email not configured)"

    body = f"""Dear {partner_name},

Your signature has been applied to a document via the YPEF Partner Document Signing Tool.

Document: {document_filename}
Date/Time: {_format_timestamp()}
Operator: {operator_name}
Audit Reference: {log_id}

This is an automated notification. Please contact the operations team if you did not expect this action.

Regards,
YourNest Operations
"""

    message = MIMEMultipart()
    message["From"] = settings.smtp_from
    message["To"] = partner_email
    message["Subject"] = f"Signature Applied — {document_filename}"
    if cc_operator and settings.smtp_user:
        message["Cc"] = settings.smtp_user
    message.attach(MIMEText(body, "plain"))

    recipients = [partner_email]
    if cc_operator and settings.smtp_user:
        recipients.append(settings.smtp_user)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, recipients, message.as_string())
        return f"sent at {_format_timestamp()}"
    except Exception as exc:
        return f"failed: {exc}"
