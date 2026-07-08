from app.core.config import settings
from app.services.email.base import EmailProvider
from app.services.email.console_provider import ConsoleEmailProvider
from app.services.email.smtp_provider import SmtpEmailProvider


def get_email_provider() -> EmailProvider:
    if settings.email_provider == "smtp":
        return SmtpEmailProvider()
    return ConsoleEmailProvider()
