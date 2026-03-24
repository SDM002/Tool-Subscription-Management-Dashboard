"""
app/models/__init__.py
CRITICAL — import all models here so SQLAlchemy metadata is populated
before create_tables() is called at startup. If you skip any model,
its table will not be created.
"""
from app.models.user import User
from app.models.subscription import Subscription
from app.models.reminder_log import ReminderLog
from app.models.chat_memory import ChatMemory

__all__ = ["User", "Subscription", "ReminderLog", "ChatMemory"]
