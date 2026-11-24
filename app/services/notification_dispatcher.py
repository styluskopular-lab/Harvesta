import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

import httpx
from sqlalchemy.orm import Session

from app.models.notification import NotificationLog
from app.models.user import User


def _send_email(recipient: str, subject: str, body: str) -> str | None:
    host = os.getenv("SMTP_HOST")
    username = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    if not host or not username or not password:
        return None

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = os.getenv("SMTP_FROM", username)
    message["To"] = recipient
    message.set_content(body)

    port = int(os.getenv("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=10) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)
    return "smtp"


def _send_sms(recipient: str, body: str) -> str | None:
    at_username = os.getenv("AT_USERNAME") or os.getenv("AFRICASTALKING_USERNAME")
    at_api_key = os.getenv("AT_API_KEY") or os.getenv("AFRICASTALKING_API_KEY")
    if at_username and at_api_key:
        payload = {"username": at_username, "to": recipient, "message": body}
        sender = os.getenv("AT_SENDER_ID") or os.getenv("AFRICASTALKING_SENDER_ID")
        if sender:
            payload["from"] = sender
        response = httpx.post(
            "https://api.africastalking.com/version1/messaging",
            data=payload,
            headers={"apiKey": at_api_key, "Accept": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        return "africas_talking"

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    if account_sid and auth_token and from_number:
        response = httpx.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
            data={"To": recipient, "From": from_number, "Body": body},
            auth=(account_sid, auth_token),
            timeout=10,
        )
        response.raise_for_status()
        return "twilio"
    return None


def dispatch_user_notification(
    db: Session,
    user: User,
    event_type: str,
    subject: str,
    body: str,
) -> list[NotificationLog]:
    preference = user.notification_preference or "email"
    channels = {
        "email": ("email",),
        "sms": ("sms",),
        "both": ("email", "sms"),
    }.get(preference)
    if channels is None:
        raise ValueError(f"Unsupported notification preference: {preference}")

    logs = []
    for channel in channels:
        recipient = user.email if channel == "email" else user.phone
        if not recipient:
            provider = "no_recipient"
            notification_status = "failed"
            error_message = f"No {channel} recipient is set on this account."
        else:
            try:
                provider = (
                    _send_email(recipient, subject, body)
                    if channel == "email"
                    else _send_sms(recipient, body)
                )
                notification_status = "sent" if provider else "recorded"
                error_message = None
                if provider is None:
                    provider = f"{channel}_unconfigured"
            except (
                OSError,
                ValueError,
                smtplib.SMTPException,
                httpx.HTTPError,
            ) as exc:
                provider = "smtp" if channel == "email" else "sms_provider"
                notification_status = "failed"
                error_message = type(exc).__name__

        log_entry = NotificationLog(
            user_id=user.id,
            channel=channel,
            event_type=event_type,
            recipient=recipient or "",
            subject=subject,
            message=body,
            provider=provider,
            status=notification_status,
            error_message=error_message,
            sent_at=datetime.now(timezone.utc)
            if notification_status == "sent"
            else None,
        )
        db.add(log_entry)
        logs.append(log_entry)

    db.commit()
    for log_entry in logs:
        db.refresh(log_entry)
    return logs
