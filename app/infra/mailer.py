"""
SMTP implementation of email sender.
"""

import asyncio
import logging
import smtplib
import ssl
from collections.abc import Iterable
from email.message import EmailMessage

from app.config import settings
from app.domain.providers.interfaces import IEmailSender

logger = logging.getLogger(__name__)


class SmtpEmailSender(IEmailSender):
    """
    SMTP implementation of email sender using blocking calls wrapped in asyncio.to_thread.
    """

    def _make_message(self, subject: str, to: str | Iterable[str], text: str, html: str | None = None) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from

        if isinstance(to, (list, tuple, set)):
            msg["To"] = ", ".join(to)
        else:
            msg["To"] = to

        msg.set_content(text)
        if html:
            msg.add_alternative(html, subtype="html")
        return msg

    def _send_sync(self, msg: EmailMessage) -> None:
        """
        Blocking synchronous SMTP sending logic.
        """
        sec = (settings.smtp_security or "starttls").lower()

        if sec == "ssl":
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_sec, context=context
            ) as s:
                if settings.smtp_user:
                    s.login(settings.smtp_user, settings.smtp_pass or "")
                s.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_sec) as s:
                if sec == "starttls":
                    s.starttls(context=ssl.create_default_context())
                if settings.smtp_user:
                    s.login(settings.smtp_user, settings.smtp_pass or "")
                s.send_message(msg)

    async def send_mail(self, subject: str, to: str | list[str], text: str, html: str | None = None) -> bool:
        """
        Sends an email asynchronously by running blocking SMTP code in a separate thread.
        """
        try:
            msg = self._make_message(subject, to, text, html)
            # Offload blocking I/O to a thread to prevent blocking the event loop
            await asyncio.to_thread(self._send_sync, msg)
            logger.info("Email sent successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


# Global instance for easy access if needed, though DI is preferred
mailer = SmtpEmailSender()


async def send_mail(subject: str, to: str | list[str], text: str, html: str | None = None) -> bool:
    """
    Convenience function that delegates to the global mailer instance.
    """
    return await mailer.send_mail(subject, to, text, html)
