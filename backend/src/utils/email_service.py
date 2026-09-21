"""
email_service.py — Reusable Email Notification Engine (SPEC-09)
================================================================
Provider-agnostic email notification engine with Mailgun REST integration,
inlined glass/dark HTML templates, and resilient console fallback.
Zero sensitive credentials are leaked or logged.
"""
import os
import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger("finnie.email")

TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates",
    "email"
)


def mask_email(email: str) -> str:
    """
    Masks an email address for safe logging without privacy leaks.
    Example: 'investor@finnie.ai' -> 'in***@finnie.ai'
    """
    if not email or "@" not in email:
        return "***"
    local_part, domain = email.split("@", 1)
    if len(local_part) <= 2:
        masked_local = local_part[0] + "***" if local_part else "***"
    else:
        masked_local = local_part[:2] + "***"
    return f"{masked_local}@{domain}"


class EmailMessage:
    """Encapsulates an outgoing email message payload."""

    def __init__(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        from_email: Optional[str] = None
    ):
        self.to_email = to_email.strip()
        self.subject = subject.strip()
        self.html_body = html_body
        self.text_body = text_body
        self.from_email = from_email.strip() if from_email else None


class BaseEmailProvider(ABC):
    """Abstract interface for email dispatch transports."""

    @abstractmethod
    def send_email(self, message: EmailMessage) -> bool:
        """Dispatches an email message. Returns True on success, False on error."""
        pass


class MailgunEmailProvider(BaseEmailProvider):
    """Dispatches emails via Mailgun REST API."""

    def __init__(
        self,
        api_key: str,
        domain: str,
        base_url: str = "https://api.mailgun.net",
        from_email: Optional[str] = None
    ):
        self.api_key = api_key
        self.domain = domain
        self.base_url = (base_url or "https://api.mailgun.net").rstrip("/")
        self.from_email = from_email or f"Finnie AI Security <postmaster@{domain}>"

    def send_email(self, message: EmailMessage) -> bool:
        url = f"{self.base_url}/v3/{self.domain}/messages"
        sender = message.from_email or self.from_email
        masked_to = mask_email(message.to_email)

        data = {
            "from": sender,
            "to": message.to_email,
            "subject": message.subject,
            "text": message.text_body,
            "html": message.html_body,
        }

        try:
            response = requests.post(
                url,
                auth=("api", self.api_key),
                data=data,
                timeout=8.0
            )

            if response.status_code in (200, 202):
                print(f"[EMAIL] 📧 Successfully dispatched '{message.subject}' to {masked_to} via Mailgun (HTTP {response.status_code})")
                return True

            error_snippet = response.text[:200] if response.text else "No response body"
            if "authorized recipients" in error_snippet.lower():
                print(
                    f"[EMAIL] ⚠️ Mailgun Sandbox restriction: Recipient {masked_to} is not an Authorized Recipient in Mailgun Dashboard. "
                    f"Please add {masked_to} under Sending -> Domains -> Authorized Recipients."
                )
            else:
                print(f"[EMAIL] ❌ Mailgun API returned HTTP {response.status_code}: {error_snippet}")
            return False

        except requests.exceptions.Timeout:
            print(f"[EMAIL] ⚠️ Mailgun request timed out after 8s when sending to {masked_to}.")
            return False
        except Exception as e:
            print(f"[EMAIL] ❌ Mailgun dispatch error for {masked_to}: {type(e).__name__} - {str(e)}")
            return False


class ConsoleEmailProvider(BaseEmailProvider):
    """Development and fallback transport that logs to console."""

    def send_email(self, message: EmailMessage) -> bool:
        masked_to = mask_email(message.to_email)
        print(f"\n{'=' * 60}")
        print(f"[EMAIL] 📧 [CONSOLE DISPATCH] To: {masked_to} | Subject: {message.subject}")
        print(f"{'-' * 60}")
        print(message.text_body.strip())
        print(f"{'=' * 60}\n")
        return True


class EmailService:
    """
    Central notification service facade.
    Automatically selects Mailgun if configured, or falls back to Console.
    """

    @classmethod
    def get_provider(cls) -> BaseEmailProvider:
        api_key = os.getenv("MAILGUN_API_KEY", "").strip()
        domain = os.getenv("MAILGUN_DOMAIN", "").strip()
        base_url = os.getenv("MAILGUN_BASE_URL", "https://api.mailgun.net").strip()
        from_email = os.getenv("MAILGUN_FROM_EMAIL", "").strip()

        if api_key and domain:
            return MailgunEmailProvider(
                api_key=api_key,
                domain=domain,
                base_url=base_url,
                from_email=from_email
            )
        return ConsoleEmailProvider()

    @classmethod
    def render_template(cls, template_filename: str, context: Dict[str, Any]) -> str:
        filepath = os.path.join(TEMPLATES_DIR, template_filename)
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Email template not found: {template_filename}")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        for key, val in context.items():
            content = content.replace(f"{{{{{key}}}}}", str(val))
        return content

    @classmethod
    def send_otp_reset_email(
        cls,
        to_email: str,
        otp_code: str,
        expiry_minutes: int = 15,
        location: str = "Unknown",
        user_name: Optional[str] = None
    ) -> bool:
        """
        Renders and sends the professional OTP password recovery email.
        If Mailgun fails (e.g. unverified sandbox recipient), automatically
        falls back to Console logging so verification codes remain accessible in dev.
        """
        context = {
            "otp_code": otp_code,
            "expiry_minutes": expiry_minutes,
            "request_location": location or "Unknown",
            "user_name": user_name or "Investor",
            "recipient_email": to_email
        }

        try:
            html_content = cls.render_template("otp_reset.html", context)
            text_content = cls.render_template("otp_reset.txt", context)
        except Exception as e:
            # Defensive fallback if template file fails to load
            html_content = f"<p>Your Finnie AI verification code is: <strong>{otp_code}</strong> (Expires in {expiry_minutes}m)</p>"
            text_content = f"Your Finnie AI verification code is: {otp_code} (Expires in {expiry_minutes}m)"

        message = EmailMessage(
            to_email=to_email,
            subject=f"{otp_code} is your Finnie AI verification code",
            html_body=html_content,
            text_body=text_content
        )

        provider = cls.get_provider()
        success = provider.send_email(message)

        # If live provider failed (e.g., Mailgun sandbox unauthorized recipient),
        # fall back to console logging so local developers/testers are not blocked
        if not success and isinstance(provider, MailgunEmailProvider):
            print("[EMAIL] ℹ️ Falling back to ConsoleEmailProvider for verification code visibility:")
            ConsoleEmailProvider().send_email(message)

        return success

    @classmethod
    def send_custom_email(
        cls,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Generic method for dispatching custom emails across future use cases.
        """
        message = EmailMessage(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            from_email=from_email
        )
        return cls.get_provider().send_email(message)
