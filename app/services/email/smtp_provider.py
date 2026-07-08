import smtplib
from email.mime.text import MIMEText

from app.core.config import settings
from app.services.email.base import EmailProvider


class SmtpEmailProvider(EmailProvider):
    """Sends real email via plain SMTP (stdlib `smtplib` — no extra
    dependency). Works with Gmail (using an App Password), Outlook,
    Yandex, a custom domain's SMTP, or SendGrid/Mailgun's SMTP relay —
    anything that speaks standard SMTP. See README.md "Email
    integration" for exact setup steps per provider.
    """

    def send_email(self, to_address: str, subject: str, body: str) -> None:
        message = MIMEText(body, "plain", "utf-8")
        message["Subject"] = subject
        message["From"] = settings.smtp_from_address or settings.smtp_username
        message["To"] = to_address

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(message["From"], [to_address], message.as_string())
