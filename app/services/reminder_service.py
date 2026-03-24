"""
app/services/reminder_service.py
APScheduler fires every N hours.
Finds subscriptions renewing within REMINDER_DAYS_BEFORE days.
Checks reminder_logs to avoid duplicate sends.
"""
import logging
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)


class ReminderService:

    def __init__(self):
        self._scheduler = AsyncIOScheduler()
        self._running = False

    def start(self):
        if self._running:
            return
        self._scheduler.add_job(
            self._check_and_send,
            trigger=IntervalTrigger(hours=settings.reminder_check_interval_hours),
            id="renewal_reminder",
            replace_existing=True,
            misfire_grace_time=3600,
        )
        self._scheduler.start()
        self._running = True
        logger.info("Reminder scheduler started (every %sh, %s days before).",
                    settings.reminder_check_interval_hours, settings.reminder_days_before)

    def stop(self):
        if self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False

    async def _check_and_send(self):
        from app.models.subscription import Subscription
        from app.models.reminder_log import ReminderLog
        from app.models.user import User
        from app.services.email_service import email_service
        from app.core.database import get_db_context
        from sqlalchemy import select

        today      = date.today()
        window_end = today + timedelta(days=settings.reminder_days_before)
        logger.info("Reminder check: %s → %s", today, window_end)

        async with get_db_context() as db:
            result = await db.execute(
                select(Subscription).join(User).where(
                    Subscription.is_active == True,  # noqa: E712
                    Subscription.renewal_date >= today,
                    Subscription.renewal_date <= window_end,
                )
            )
            subs = result.scalars().all()
            sent = 0

            for sub in subs:
                # Skip if already reminded for this renewal cycle
                check = await db.execute(
                    select(ReminderLog).where(
                        ReminderLog.subscription_id == sub.id,
                        ReminderLog.renewal_date == sub.renewal_date,
                        ReminderLog.status == "sent",
                    )
                )
                if check.scalar_one_or_none():
                    continue

                user_r = await db.execute(select(User).where(User.id == sub.user_id))
                user   = user_r.scalar_one_or_none()
                if not user:
                    continue

                days_left = (sub.renewal_date - today).days
                success   = await email_service.send_renewal_reminder(
                    to_email=user.email, user_name=user.full_name,
                    tool_name=sub.tool_name,
                    renewal_date=sub.renewal_date.strftime("%B %d, %Y"),
                    days_left=days_left, price=sub.price,
                    currency=sub.currency, billing_cycle=sub.billing_cycle,
                )
                db.add(ReminderLog(
                    user_id=sub.user_id, subscription_id=sub.id,
                    renewal_date=sub.renewal_date,
                    status="sent" if success else "failed",
                    error_message=None if success else "SMTP failed",
                ))
                if success:
                    sent += 1

            logger.info("Reminder check done — sent %d email(s).", sent)

    async def trigger_now(self) -> dict:
        await self._check_and_send()
        return {"status": "ok", "message": "Reminder check triggered"}


reminder_service = ReminderService()
