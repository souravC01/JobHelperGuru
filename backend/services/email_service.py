import smtplib
from email.message import EmailMessage
from typing import Any, Dict, List, Optional
import urllib.parse


class EmailTransport:
    """Base interface for email delivery transports."""

    def send(self, recipient: str, subject: str, text_body: str) -> None:
        raise NotImplementedError


class FakeEmailTransport(EmailTransport):
    """In-memory email transport for unit tests and local isolation."""

    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []

    def send(self, recipient: str, subject: str, text_body: str) -> None:
        self.sent_messages.append({
            "recipient": recipient,
            "subject": subject,
            "body": text_body,
        })

    def get_last_verification_token(self, recipient: str) -> Optional[str]:
        import re
        for msg in reversed(self.sent_messages):
            if msg["recipient"].lower() == recipient.lower() and "verify" in msg["subject"].lower():
                m = re.search(r"[?&]token=([a-zA-Z0-9_-]+)", msg["body"])
                if m:
                    return m.group(1)
        return None

    def get_last_reset_token(self, recipient: str) -> Optional[str]:
        import re
        for msg in reversed(self.sent_messages):
            if msg["recipient"].lower() == recipient.lower() and "reset" in msg["subject"].lower():
                m = re.search(r"[?&]token=([a-zA-Z0-9_-]+)", msg["body"])
                if m:
                    return m.group(1)
        return None


class SMTPEmailTransport(EmailTransport):
    """Standard SMTP email transport for production delivery."""

    def __init__(
        self,
        host: str,
        port: int = 587,
        user: Optional[str] = None,
        password: Optional[str] = None,
        from_address: Optional[str] = None,
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_address = from_address or user or "noreply@jobhelper.guru"
        self.use_tls = use_tls

    def send(self, recipient: str, subject: str, text_body: str) -> None:
        msg = EmailMessage()
        msg["From"] = self.from_address
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(text_body)

        with smtplib.SMTP(self.host, self.port) as server:
            if self.use_tls:
                server.starttls()
            if self.user and self.password:
                server.login(self.user, self.password)
            server.send_message(msg)


class EmailService:
    """Service for dispatching transactional authentication emails."""

    def __init__(self, transport: Optional[EmailTransport] = None):
        self.transport = transport or FakeEmailTransport()

    def send_verification(self, recipient: str, token: str, app_url: str = "http://localhost:5173") -> None:
        clean_url = app_url.rstrip("/")
        link = f"{clean_url}/verify-email?token={token}"
        subject = "Verify your JobHelperGuru account"
        body = (
            f"Hello,\n\n"
            f"Please verify your JobHelperGuru account by clicking the link below:\n"
            f"{link}\n\n"
            f"This link expires in 30 minutes.\n"
            f"If you did not sign up for JobHelperGuru, please ignore this email."
        )
        self.transport.send(recipient=recipient, subject=subject, text_body=body)

    def send_password_reset(self, recipient: str, token: str, app_url: str = "http://localhost:5173") -> None:
        clean_url = app_url.rstrip("/")
        link = f"{clean_url}/reset-password?token={token}"
        subject = "Reset your JobHelperGuru password"
        body = (
            f"Hello,\n\n"
            f"We received a request to reset your JobHelperGuru password.\n"
            f"Please click the link below to set a new password:\n"
            f"{link}\n\n"
            f"This link expires in 30 minutes.\n"
            f"If you did not request a password reset, please ignore this email."
        )
        self.transport.send(recipient=recipient, subject=subject, text_body=body)
