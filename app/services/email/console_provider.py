import logging

from app.services.email.base import EmailProvider

logger = logging.getLogger("email")


class ConsoleEmailProvider(EmailProvider):
    """Prints the email to the server log instead of actually sending it.
    Use this for local development so you're not depending on real SMTP
    credentials while testing the sign-in flow. Switch
    EMAIL_PROVIDER=smtp in .env when you're ready for real emails."""

    def send_email(self, to_address: str, subject: str, body: str) -> None:
        logger.warning("=== DEV EMAIL to %s: %s | %s ===", to_address, subject, body)
        print(f"\n=== [DEV EMAIL] To: {to_address} | Subject: {subject}\n{body}\n===\n")
