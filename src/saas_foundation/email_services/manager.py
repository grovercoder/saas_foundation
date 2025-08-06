import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional



class EmailManager:
    def __init__(self, logger: Any):
        self.logger = logger

        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "True").lower() == "true"
        self.smtp_sender_email = os.getenv("SMTP_SENDER_EMAIL")

        if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.smtp_sender_email]):
            self.logger.warning("SMTP environment variables are not fully configured. Email sending may fail.")

    

    def send_email(
        self,
        to_email: str,
        subject: str,
        text_content: Optional[str] = None,
        html_content: Optional[str] = None
    ):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.smtp_sender_email
        msg["To"] = to_email

        if text_content:
            text_part = MIMEText(text_content, "plain")
            msg.attach(text_part)

        if html_content:
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.smtp_sender_email, to_email, msg.as_string())
            self.logger.info(f"Email sent successfully to {to_email} with subject '{subject}'.")
        except Exception as e:
            self.logger.error(f"Failed to send email to {to_email} with subject '{subject}': {e}")
            raise
