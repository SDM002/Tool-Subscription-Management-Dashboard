"""
app/services/reminder_service.py  [NEW]

APScheduler-powered renewal reminder system.

How it works:
1. Scheduler fires every REMINDER_CHECK_INTERVAL_HOURS hours.
2. Queries all active subscriptions with renewal_date within
   REMINDER_DAYS_BEFORE days.
3. Checks ReminderLog to avoid duplicate sends for the same
   (subscription_id, renewal_date) pair.
4. Sends email via EmailService and logs the result.

Required env vars:
  REMINDER_DAYS_BEFORE          (default: 7)
  REMINDER_CHECK_INTERVAL_HOURS (default: 24)
  + all SMTP_* variables
"""

import logging
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db_context

logger = logging.getLogger(__name__)


class ReminderService:

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._scheduler.add_job(
            self._check_and_send_reminders,
            trigger=IntervalTrigger(hours=settings.reminder_check_interval_hours),
            id="renewal_reminder",
            replace_existing=True,
            misfire_grace_time=3600,
        )
        self._scheduler.start()
        self._running = True
        logger.info(
            "Reminder scheduler started — checking every %sh, reminding %s days before renewal.",
            settings.reminder_check_interval_hours,
            settings.reminder_days_before,
        )

    def stop(self) -> None:
        if self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False

    async def _check_and_send_reminders(self) -> None:
        """Core job: find due subscriptions and send reminder emails."""
        # Import inside function to avoid circular imports at module load
        from app.models.subscription import Subscription
        from app.models.reminder_log import ReminderLog
        from app.models.user import User
        from app.services.email_service import email_service

        today = date.today()
        window_end = today + timedelta(days=settings.reminder_days_before)

        logger.info("Reminder check: scanning renewals between %s and %s", today, window_end)

        async with get_db_context() as db:
            # All active subs renewing within the window
            stmt = (
                select(Subscription)
                .join(User, User.id == Subscription.user_id)
                .where(
                    Subscription.is_active == True,        # noqa: E712
                    Subscription.renewal_date >= today,
                    Subscription.renewal_date <= window_end,
                )
            )
            result = await db.execute(stmt)
            subs = result.scalars().all()

            sent_count = 0
            for sub in subs:
                # Check if we already sent a reminder for this renewal cycle
                already_sent = await db.execute(
                    select(ReminderLog).where(
                        ReminderLog.subscription_id == sub.id,
                        ReminderLog.renewal_date == sub.renewal_date,
                        ReminderLog.status == "sent",
                    )
                )
                if already_sent.scalar_one_or_none():
                    continue  # skip — already reminded

                # Fetch user email
                user_result = await db.execute(
                    select(User).where(User.id == sub.user_id)
                )
                user = user_result.scalar_one_or_none()
                if not user:
                    continue

                days_left = (sub.renewal_date - today).days

                # Send the email
                success = await email_service.send_renewal_reminder(
                    to_email=user.email,
                    user_name=user.full_name,
                    tool_name=sub.tool_name,
                    renewal_date=sub.renewal_date.strftime("%B %d, %Y"),
                    days_left=days_left,
                    price=sub.price,
                    currency=sub.currency,
                    billing_cycle=sub.billing_cycle,
                )

                # Log the attempt
                log = ReminderLog(
                    user_id=sub.user_id,
                    subscription_id=sub.id,
                    renewal_date=sub.renewal_date,
                    status="sent" if success else "failed",
                    error_message=None if success else "SMTP send failed",
                )
                db.add(log)
                if success:
                    sent_count += 1

            await db.flush()
            logger.info("Reminder check complete — sent %d email(s).", sent_count)

    async def trigger_now(self) -> dict:
        """Manually trigger the reminder check (useful for testing)."""
        await self._check_and_send_reminders()
        return {"status": "ok", "message": "Reminder check triggered manually"}


reminder_service = ReminderService()
