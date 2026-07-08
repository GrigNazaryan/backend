from abc import ABC, abstractmethod


class EmailProvider(ABC):
    """Anything that can send an email. Swapping providers (SMTP/Gmail,
    SendGrid, Mailgun, Amazon SES, etc.) means writing one class that
    implements this and pointing EMAIL_PROVIDER at it in .env — nothing
    else in the codebase needs to change."""

    @abstractmethod
    def send_email(self, to_address: str, subject: str, body: str) -> None:
        """Send a plain-text email. Should raise an exception on failure
        so the caller can surface a real error instead of silently
        pretending the code was sent."""
        raise NotImplementedError
