"""Transactional email via Mailtrap Python SDK."""

from __future__ import annotations

import logging

import mailtrap as mt
from mailtrap.exceptions import MailtrapError

from app.config.settings import Settings

_log = logging.getLogger(__name__)


def send_transactional_email(
    settings: Settings,
    *,
    to_email: str,
    subject: str,
    text: str,
    html: str | None = None,
) -> None:
    """Send one message through Mailtrap Sending API."""
    if settings.auth_dev_auto_verify_email:
        _log.debug(
            "Mail send skipped (dev auto-verify)",
            extra={"event": "mail_skipped_dev_auto_verify"},
        )
        return
    if not settings.mailtrap_api_token:
        raise RuntimeError("mailtrap_api_token is not configured")

    client = mt.MailtrapClient(token=settings.mailtrap_api_token)
    mail = mt.Mail(
        sender=mt.Address(email=settings.mail_from_email, name=settings.mail_from_name),
        to=[mt.Address(email=to_email)],
        subject=subject,
        text=text,
        html=html,
    )
    try:
        client.send(mail)
    except MailtrapError as e:
        _log.warning(
            "Mailtrap send failed",
            extra={"event": "mail_send_failed", "error_type": type(e).__name__, "to_email": to_email},
        )
        raise
