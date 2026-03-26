import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:

    async def send_email(self, to_email: str, subject: str, html_body: str, text_body: str | None = None) -> bool:
        if not settings.smtp_username or not settings.smtp_password:
            logger.warning("SMTP not configured — skipping email to %s", to_email)
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"]      = to_email
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
            logger.error("Email failed to %s: %s", to_email, exc)
            return False

    async def send_renewal_reminder(
        self, to_email: str, user_name: str,
        tool_name: str, renewal_date: str,
        days_left: int, price: float, currency: str, billing_cycle: str,
    ) -> bool:
        subject = f"🔔 {tool_name} renews in {days_left} day{'s' if days_left != 1 else ''}"
        color   = "#e53e3e" if days_left <= 3 else "#d97706" if days_left <= 7 else "#38a169"
        html = f"""
        <div style="font-family:sans-serif;max-width:520px;margin:0 auto;background:#f8f9fa;padding:20px;border-radius:12px">
          <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:24px;border-radius:10px;text-align:center;margin-bottom:20px">
            <h1 style="color:white;margin:0;font-size:22px">Renewal Reminder</h1>
          </div>
          <div style="background:white;padding:24px;border-radius:10px">
            <p style="color:#333">Hi <strong>{user_name}</strong>,</p>
            <p style="color:#555"><strong>{tool_name}</strong> renews in
               <strong style="color:{color}">{days_left} day{'s' if days_left != 1 else ''}</strong>.</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0">
              <tr><td style="padding:8px;color:#666">Tool</td>
                  <td style="padding:8px;font-weight:600;text-align:right">{tool_name}</td></tr>
              <tr style="background:#f8f9fa">
                  <td style="padding:8px;color:#666">Renewal Date</td>
                  <td style="padding:8px;font-weight:600;text-align:right">{renewal_date}</td></tr>
              <tr><td style="padding:8px;color:#666">Amount</td>
                  <td style="padding:8px;font-weight:600;text-align:right">{currency} {price:.2f}/{billing_cycle}</td></tr>
            </table>
            <p style="color:#888;font-size:13px">If you no longer need this, cancel before the renewal date.</p>
          </div>
        </div>"""
        text = f"Hi {user_name},\n\n{tool_name} renews in {days_left} day(s) on {renewal_date}.\nAmount: {currency} {price:.2f}/{billing_cycle}\n"
        return await self.send_email(to_email, subject, html, text)


email_service = EmailService()
