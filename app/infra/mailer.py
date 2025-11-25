from email.message import EmailMessage
import smtplib, ssl
from typing import Iterable
from app.config import settings
from app.core.logging import lg

def _make_message(subject: str, to: str | Iterable[str], text: str, html: str | None = None) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = ", ".join(to) if isinstance(to, (list, tuple, set)) else to
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")
    return msg

def send_mail(subject: str, to: str, text: str, html: str | None = None) -> None:
    msg = _make_message(subject, to, text, html)
    sec = (settings.smtp_security or "starttls").lower()

    try:
        if sec == "ssl":
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_sec, context=context) as s:
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
        lg("app").bind(scope="mail").info("mail.sent")
    except Exception as e:
        lg("app").bind(scope="mail", err=type(e).__name__).error(f"mail.error: {e}")
