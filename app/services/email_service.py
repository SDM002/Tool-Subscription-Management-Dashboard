"""
app/services/email_service.py  [NEW]

Async SMTP email service using aiosmtplib.
Configure via environment variables — no hardcoded credentials.

Required env vars:
  SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
  SMTP_FROM_EMAIL, SMTP_FROM_NAME, SMTP_TLS
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> bool:
        """
        Send an email via SMTP.
        Returns True on success, False on failure (logs the error).
        """
        if not settings.smtp_username or not settings.smtp_password:
            logger.warning(
                "Email not configured — skipping send to %s (subject: %s)",
                to_email,
                subject,
            )
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                start_tls=settings.smtp_tls,
            )
            logger.info("Email sent to %s: %s", to_email, subject)
            return True

        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to_email, exc)
            return False

    async def send_renewal_reminder(
        self,
        to_email: str,
        user_name: str,
        tool_name: str,
        renewal_date: str,
        days_left: int,
        price: float,
        currency: str,
        billing_cycle: str,
    ) -> bool:
        subject = f"ð Renewal reminder: {tool_name} renews in {days_left} day{'s' if days_left != 1 else ''}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                     background: #f8f9fa; margin: 0; padding: 20px;">
          <div style="max-width: 560px; margin: 0 auto; background: white;
                      border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 32px; text-align: center;">
              <h1 style="color: white; margin: 0; font-size: 24px;">Renewal Reminder</h1>
              <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0;">
                Your subscription is renewing soon
              </p>
            </div>

            <!-- Body -->
            <div style="padding: 32px;">
              <p style="color: #333; font-size: 16px;">Hi {user_name},</p>
              <p style="color: #555; font-size: 15px; line-height: 1.6;">
                Your <strong>{tool_name}</strong> subscription is due for renewal
                in <strong>{days_left} day{'s' if days_left != 1 else ''}</strong>.
              </p>

              <!-- Info card -->
              <div style="background: #f0f4ff; border-left: 4px solid #667eea;
                          border-radius: 8px; padding: 20px; margin: 24px 0;">
                <table style="width: 100%; border-collapse: collapse;">
                  <tr>
                    <td style="color: #666; padding: 6px 0; font-size: 14px;">Tool</td>
                    <td style="color: #333; font-weight: 600; font-size: 14px; text-align: right;">
                      {tool_name}
                    </td>
                  </tr>
                  <tr>
                    <td style="color: #666; padding: 6px 0; font-size: 14px;">Renewal Date</td>
                    <td style="color: #333; font-weight: 600; font-size: 14px; text-align: right;">
                      {renewal_date}
                    </td>
                  </tr>
                  <tr>
                    <td style="color: #666; padding: 6px 0; font-size: 14px;">Amount</td>
                    <td style="color: #333; font-weight: 600; font-size: 14px; text-align: right;">
                      {currency} {price:.2f} / {billing_cycle}
                    </td>
                  </tr>
                  <tr>
                    <td style="color: #666; padding: 6px 0; font-size: 14px;">Days Left</td>
                    <td style="color: {'#e53e3e' if days_left <= 3 else '#ed8936' if days_left <= 7 else '#38a169'};
                                font-weight: 700; font-size: 14px; text-align: right;">
                      {days_left} day{'s' if days_left != 1 else ''}
                    </td>
                  </tr>
                </table>
              </div>

              <p style="color: #555; font-size: 14px; line-height: 1.6;">
                If you no longer need this subscription, now is a good time to cancel
                before the renewal date to avoid being charged.
              </p>
            </div>

            <!-- Footer -->
            <div style="background: #f8f9fa; padding: 20px; text-align: center;
                        border-top: 1px solid #eee;">
              <p style="color: #999; font-size: 12px; margin: 0;">
                Sent by Tool Subscription Dashboard
              </p>
            </div>
          </div>
        </body>
        </html>
        """

        text_body = (
            f"Hi {user_name},\n\n"
            f"Your {tool_name} subscription renews in {days_left} day(s) on {renewal_date}.\n"
            f"Amount: {currency} {price:.2f} / {billing_cycle}\n\n"
            f"Log in to your dashboard to manage this subscription.\n"
        )

        return await self.send_email(to_email, subject, html_body, text_body)


email_service = EmailService()
