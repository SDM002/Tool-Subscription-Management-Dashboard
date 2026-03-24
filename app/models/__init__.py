"""
app/models/__init__.py  [NEW]

Import all models here so that SQLAlchemy's metadata registry
is populated before create_tables() is called at startup.
"""

from app.models.user import User
from app.models.subscription import Subscription
from app.models.reminder_log import ReminderLog
from app.models.chat_memory import ChatMemory

__all__ = ["User", "Subscription", "ReminderLog", "ChatMemory"]
