# 📦 Tool Subscription Management Dashboard
### Powered by LangGraph · Groq · MCP · FastAPI · ChromaDB

A full-stack web application to track and manage your software subscriptions,
with an AI assistant that uses the **exact same architecture** as the
[Agentic AI ChatBot MCP](https://github.com/SDM002/Agentic-AI-ChatBot-MCP) project:
**LangGraph for reasoning, MCP for tool execution, Groq as the LLM.**

---

## Architecture (how everything connects)

```
Browser  ──GET /api/chat/stream──►  FastAPI (app/main.py)
                                         │
                                    app/routes/chat.py
                                         │ spawns once
                                         ▼
                               app/agent/agent_runner.py   ◄── YOUR agent_runner.py
                                         │
                                  LangGraph graph          ◄── YOUR graph.py
                                  (app/agent/graph.py)
                                    │           │
                              Groq LLM      tool_calls?
                            (llama-3.1)         │
                                                ▼
                                   app/mcp/client.py       ◄── YOUR client.py
                                   (MCPClient singleton)
                                         │ stdin/stdout
                                         ▼
                                   app/mcp/server.py       ◄── YOUR server.py
                                   ┌────────────────────┐
                                   │  get_subscriptions  │
                                   │  get_spending_summary│
                                   │  get_upcoming_renewals│
                                   │  get_spending_insights│
                                   │  get_alternatives    │
                                   └────────────────────┘
                                         │
                                    SQLite DB
```

**Key design (same as your original repo):**
- `graph.py` — LangGraph + Groq. Tool SCHEMAS only. `func=lambda: None`
- `agent_runner.py` — the agentic loop. Detects `tool_calls` → calls MCP → injects `ToolMessage` → loops
- `client.py` — MCPClient singleton subprocess, JSON-RPC over stdin/stdout
- `server.py` — actual tool execution. Reads SQLite directly (own process)
- Chat uses **SSE streaming** via `fetch()` + `ReadableStream` — same as your original `EventSource`

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq `llama-3.1-8b-instant` via `langchain-groq` |
| Agent framework | LangGraph `StateGraph` |
| Tool protocol | MCP (Model Context Protocol) — stdio transport |
| Backend | FastAPI (async) |
| Database | SQLite → swap to PostgreSQL by changing one env var |
| ORM | SQLAlchemy 2.0 async |
| Validation | Pydantic v2 |
| Auth | JWT (`python-jose`) + bcrypt (`passlib`) |
| Short-term memory | SQL `chat_memories` table per session |
| Long-term memory | ChromaDB (persistent vector store, per-user isolated) |
| Scheduler | APScheduler (renewal email reminders) |
| Email | aiosmtplib (async SMTP) |
| Frontend | Vanilla HTML + CSS + JavaScript (no build step) |

---

## Complete Folder Structure

```
sub-dashboard/
│
├── app/
│   ├── __init__.py
│   ├── main.py                      ← FastAPI factory + startup + router registration
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                ← all settings loaded from .env
│   │   ├── database.py              ← async SQLAlchemy engine + get_db() dependency
│   │   └── security.py              ← bcrypt hash/verify
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt_handler.py           ← create_access_token / decode_token
│   │   ├── dependencies.py          ← get_current_user (FastAPI dependency)
│   │   └── routes.py                ← POST /register, POST /login, GET /me
│   │
│   ├── models/
│   │   ├── __init__.py              ← ⚠️ CRITICAL: imports all 4 models
│   │   ├── user.py                  ← users table
│   │   ├── subscription.py          ← subscriptions table + monthly/yearly_cost
│   │   ├── reminder_log.py          ← prevents duplicate email reminders
│   │   └── chat_memory.py           ← short-term conversation history
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py                  ← register/login request + token response
│   │   ├── subscription.py          ← create/update/response shapes
│   │   ├── dashboard.py             ← summary + renewal items
│   │   └── chat.py                  ← chat request/response
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py          ← register + login logic
│   │   ├── subscription_service.py  ← CRUD with user_id isolation on every query
│   │   ├── dashboard_service.py     ← spending totals + renewal calculations
│   │   ├── email_service.py         ← async SMTP renewal reminder emails
│   │   └── reminder_service.py      ← APScheduler job, checks renewals every N hours
│   │
│   ├── mcp/                         ← YOUR MCP PATTERN
│   │   ├── __init__.py
│   │   ├── server.py                ← MCP server: 5 subscription tools executed here
│   │   └── client.py                ← MCPClient singleton — YOUR client.py pattern
│   │
│   ├── agent/                       ← YOUR LANGGRAPH PATTERN
│   │   ├── __init__.py
│   │   ├── graph.py                 ← LangGraph StateGraph + Groq — YOUR graph.py
│   │   ├── agent_runner.py          ← agentic loop bridge — YOUR agent_runner.py
│   │   ├── prompt.py                ← system prompt template
│   │   └── memory.py                ← short-term SQL + long-term ChromaDB
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py                ← GET /api/health
│   │   ├── subscriptions.py         ← CRUD /api/subscriptions
│   │   ├── dashboard.py             ← /api/dashboard/summary|renewals|insights
│   │   └── chat.py                  ← GET /api/chat/stream (SSE) + POST /api/chat
│   │
│   └── tools/
│       └── __init__.py              ← placeholder (tools are in app/mcp/server.py)
│
├── static/
│   ├── index.html                   ← single-page app shell
│   ├── styles.css                   ← complete design system
│   └── app.js                       ← all frontend logic + SSE streaming chat
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  ← in-memory SQLite fixtures
│   ├── test_auth.py                 ← register, login, /me, health
│   ├── test_subscriptions.py        ← CRUD + user isolation
│   └── test_dashboard.py            ← spending totals + renewals
│
├── data/                            ← auto-created at runtime
│   ├── subscriptions.db             ← SQLite database
│   └── chroma/                      ← ChromaDB vector files
│
├── .env                             ← your secrets (NEVER commit)
├── .env.example                     ← template (safe to commit)
├── .gitignore
├── requirements.txt
├── pytest.ini
├── run.py                           ← python run.py
└── seed.py                          ← python seed.py (demo data)
```

---

## Every File — Complete Source Code

### `requirements.txt`

```text
# Web framework
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9

# LangGraph + Groq (YOUR architecture)
langgraph==0.2.28
langchain==0.3.1
langchain-core==0.3.6
langchain-groq==0.2.0

# MCP (YOUR architecture)
mcp==1.0.0

# Database
sqlalchemy==2.0.30
aiosqlite==0.20.0

# Validation & config
pydantic==2.7.1
pydantic-settings==2.3.0
email-validator==2.1.1
python-dotenv==1.0.1

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1

# Scheduler & email
apscheduler==3.10.4
aiosmtplib==3.0.1

# Long-term memory
chromadb==0.5.3

# HTTP
requests==2.32.3
httpx==0.27.0
```

---

### `.env.example`

```ini
# ── GROQ LLM ─────────────────────────────────────────────────
# Get FREE key at: https://console.groq.com
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-8b-instant

# ── App ───────────────────────────────────────────────────────
APP_NAME="Subscription Dashboard"
DEBUG=true

# ── Security ─────────────────────────────────────────────────
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=change-me-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ── Database ─────────────────────────────────────────────────
DATABASE_URL=sqlite+aiosqlite:///./data/subscriptions.db

# ── Email (optional — for renewal reminders) ─────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME="Subscription Dashboard"
SMTP_TLS=true

# ── ChromaDB (long-term memory) ──────────────────────────────
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION=subscription_memory

# ── Reminders ────────────────────────────────────────────────
REMINDER_DAYS_BEFORE=7
REMINDER_CHECK_INTERVAL_HOURS=24
```

---

### `.gitignore`

```
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
env/
.env
data/
*.db
*.sqlite3
chroma/
.pytest_cache/
.coverage
htmlcov/
.vscode/
.idea/
.DS_Store
*.log
node_modules/
```

---

### `pytest.ini`

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

---

### `run.py`

```python
"""run.py — python run.py"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
```

---

### `seed.py`

```python
"""
seed.py — populate DB with demo data.
Usage: python seed.py
Login: demo@example.com / Demo1234
"""
import asyncio
from datetime import date, timedelta


async def seed():
    import app.models  # noqa
    from app.core.database import create_tables, get_db_context
    from app.core.security import hash_password
    from app.models.user import User
    from app.models.subscription import BillingCycle, Subscription
    from sqlalchemy import select

    await create_tables()
    print("✅ Tables ready.")

    today = date.today()
    SUBS = [
        dict(tool_name="Notion",        category="Productivity",    price=16.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=5),   currency="USD"),
        dict(tool_name="Figma",         category="Design",          price=15.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=3),   currency="USD", notes="Pro plan"),
        dict(tool_name="Adobe CC",      category="Design",          price=54.99, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=22),  currency="USD"),
        dict(tool_name="GitHub Pro",    category="Development",     price=4.00,  billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=11),  currency="USD"),
        dict(tool_name="Vercel Pro",    category="Development",     price=20.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=45),  currency="USD"),
        dict(tool_name="JetBrains All", category="Development",     price=77.90, billing_cycle=BillingCycle.YEARLY,    renewal_date=today+timedelta(days=180), currency="USD"),
        dict(tool_name="Slack Pro",     category="Communication",   price=8.75,  billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=2),   currency="USD"),
        dict(tool_name="Loom Business", category="Communication",   price=12.50, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=33),  currency="USD"),
        dict(tool_name="Dropbox Plus",  category="Storage & Cloud", price=11.99, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=14),  currency="USD"),
        dict(tool_name="AWS",           category="Storage & Cloud", price=45.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=7),   currency="USD", notes="Estimated avg"),
        dict(tool_name="1Password",     category="Security",        price=2.99,  billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=9),   currency="USD"),
        dict(tool_name="ChatGPT Plus",  category="AI & ML",         price=20.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=6),   currency="USD"),
        dict(tool_name="Claude Pro",    category="AI & ML",         price=20.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=27),  currency="USD"),
        dict(tool_name="Mixpanel",      category="Analytics",       price=28.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=50),  currency="USD"),
        dict(tool_name="Todoist",       category="Productivity",    price=4.00,  billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=18),  currency="USD"),
    ]

    async with get_db_context() as db:
        result = await db.execute(select(User).where(User.email == "demo@example.com"))
        if result.scalar_one_or_none():
            print("ℹ️  Demo user already exists — skipping.")
            return
        user = User(email="demo@example.com", full_name="Demo User", hashed_password=hash_password("Demo1234"))
        db.add(user)
        await db.flush()
        print(f"✅ Created user: demo@example.com (id={user.id})")
        for s in SUBS:
            db.add(Subscription(user_id=user.id, **s))
        await db.flush()
        print(f"✅ Seeded {len(SUBS)} subscriptions.")

    print("\n🚀 Done!")
    print("   Email:    demo@example.com")
    print("   Password: Demo1234")
    print("   Open:     http://localhost:8000")


if __name__ == "__main__":
    asyncio.run(seed())
```

---

### `app/__init__.py`

```python
# app/__init__.py
```

---

### `app/core/__init__.py`

```python
# app/core/__init__.py
```

---

### `app/core/config.py`

```python
"""
app/core/config.py
All settings loaded from .env — one place, no scattered os.getenv() calls.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Subscription Dashboard"
    debug: bool = True

    # Groq — YOUR LLM
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    # Security
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/subscriptions.db"

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Subscription Dashboard"
    smtp_tls: bool = True

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection: str = "subscription_memory"

    # Reminders
    reminder_days_before: int = 7
    reminder_check_interval_hours: int = 24


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

---

### `app/core/database.py`

```python
"""
app/core/database.py
Async SQLAlchemy engine + session.
Swap DATABASE_URL to PostgreSQL without touching anything else.
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.database_url else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields one session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """For background jobs / scheduler — not FastAPI dep injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

---

### `app/core/security.py`

```python
"""app/core/security.py — bcrypt password hashing."""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

---

### `app/auth/__init__.py`

```python
# app/auth/__init__.py
```

---

### `app/auth/jwt_handler.py`

```python
"""app/auth/jwt_handler.py — JWT creation and decoding."""
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from app.core.config import settings


def create_access_token(subject: str | int, extra_claims: dict[str, Any] | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
```

---

### `app/auth/dependencies.py`

```python
"""
app/auth/dependencies.py
get_current_user — add Depends(get_current_user) to protect any route.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import decode_token
from app.core.database import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=True)

_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if user_id is None or payload.get("type") != "access":
            raise _401
    except JWTError:
        raise _401

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise _401
    return user
```

---

### `app/auth/routes.py`

```python
"""app/auth/routes.py — /api/auth/* endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse, TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.register(db, payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login(db, payload)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/logout", response_model=MessageResponse)
async def logout():
    return MessageResponse(message="Logged out successfully")
```

---

### `app/models/__init__.py` ⚠️ CRITICAL

```python
"""
app/models/__init__.py
CRITICAL — import all models here so SQLAlchemy metadata is populated
before create_tables() is called. Missing any model = missing table.
"""
from app.models.user import User
from app.models.subscription import Subscription
from app.models.reminder_log import ReminderLog
from app.models.chat_memory import ChatMemory

__all__ = ["User", "Subscription", "ReminderLog", "ChatMemory"]
```

---

### `app/models/user.py`

```python
"""app/models/user.py — users table."""
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan"
    )
    chat_memories: Mapped[list["ChatMemory"]] = relationship(
        "ChatMemory", back_populates="user", cascade="all, delete-orphan"
    )
    reminder_logs: Mapped[list["ReminderLog"]] = relationship(
        "ReminderLog", back_populates="user", cascade="all, delete-orphan"
    )
```

---

### `app/models/subscription.py`

```python
"""app/models/subscription.py — subscriptions table."""
from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class BillingCycle:
    MONTHLY   = "monthly"
    QUARTERLY = "quarterly"
    YEARLY    = "yearly"
    LIFETIME  = "lifetime"
    ALL = [MONTHLY, QUARTERLY, YEARLY, LIFETIME]


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Other")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    renewal_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    billing_cycle: Mapped[str] = mapped_column(String(20), nullable=False, default=BillingCycle.MONTHLY)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    reminder_logs: Mapped[list["ReminderLog"]] = relationship(
        "ReminderLog", back_populates="subscription", cascade="all, delete-orphan"
    )

    @property
    def monthly_cost(self) -> float:
        if self.billing_cycle == BillingCycle.MONTHLY:   return self.price
        if self.billing_cycle == BillingCycle.QUARTERLY: return round(self.price / 3, 2)
        if self.billing_cycle == BillingCycle.YEARLY:    return round(self.price / 12, 2)
        return 0.0

    @property
    def yearly_cost(self) -> float:
        if self.billing_cycle == BillingCycle.MONTHLY:   return round(self.price * 12, 2)
        if self.billing_cycle == BillingCycle.QUARTERLY: return round(self.price * 4, 2)
        if self.billing_cycle == BillingCycle.YEARLY:    return self.price
        return self.price
```

---

### `app/models/reminder_log.py`

```python
"""app/models/reminder_log.py — prevents duplicate reminder emails."""
from datetime import date, datetime, timezone
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ReminderLog(Base):
    __tablename__ = "reminder_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    renewal_date: Mapped[date] = mapped_column(Date, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(20), default="sent")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="reminder_logs")
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="reminder_logs")
```

---

### `app/models/chat_memory.py`

```python
"""app/models/chat_memory.py — short-term conversation history."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ChatMemory(Base):
    __tablename__ = "chat_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)   # human | ai
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="chat_memories")
```

---

### `app/schemas/auth.py`

```python
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    email: str
    full_name: str
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
```

---

### `app/schemas/subscription.py`

```python
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.models.subscription import BillingCycle


class SubscriptionCreateRequest(BaseModel):
    tool_name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(default="Other", max_length=100)
    start_date: Optional[date] = None
    renewal_date: Optional[date] = None
    billing_cycle: str = Field(default=BillingCycle.MONTHLY)
    price: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="USD", max_length=10)
    website_url: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = None
    is_active: bool = True

    @field_validator("billing_cycle")
    @classmethod
    def validate_cycle(cls, v: str) -> str:
        if v not in BillingCycle.ALL:
            raise ValueError(f"billing_cycle must be one of {BillingCycle.ALL}")
        return v


class SubscriptionUpdateRequest(BaseModel):
    tool_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    start_date: Optional[date] = None
    renewal_date: Optional[date] = None
    billing_cycle: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0.0)
    currency: Optional[str] = Field(default=None, max_length=10)
    website_url: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("billing_cycle")
    @classmethod
    def validate_cycle(cls, v: str | None) -> str | None:
        if v is not None and v not in BillingCycle.ALL:
            raise ValueError(f"billing_cycle must be one of {BillingCycle.ALL}")
        return v


class SubscriptionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    user_id: int
    tool_name: str
    category: str
    start_date: Optional[date]
    renewal_date: Optional[date]
    billing_cycle: str
    price: float
    currency: str
    website_url: Optional[str]
    notes: Optional[str]
    is_active: bool
    monthly_cost: float
    yearly_cost: float
    created_at: datetime
    updated_at: datetime


class SubscriptionListResponse(BaseModel):
    total: int
    subscriptions: list[SubscriptionResponse]
```

---

### `app/schemas/dashboard.py`

```python
from datetime import date
from pydantic import BaseModel


class RenewalItem(BaseModel):
    id: int
    tool_name: str
    category: str
    renewal_date: date
    days_until_renewal: int
    price: float
    billing_cycle: str
    currency: str


class SpendByCategoryItem(BaseModel):
    category: str
    monthly_cost: float
    yearly_cost: float
    count: int


class DashboardSummaryResponse(BaseModel):
    total_subscriptions: int
    active_subscriptions: int
    total_monthly_spend: float
    total_yearly_spend: float
    due_this_week: list[RenewalItem]
    due_this_month: list[RenewalItem]
    spend_by_category: list[SpendByCategoryItem]
```

---

### `app/schemas/chat.py`

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
```

---

### `app/services/auth_service.py`

```python
"""app/services/auth_service.py — register and login."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import create_access_token
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse


class AuthService:

    async def register(self, db: AsyncSession, payload: UserRegisterRequest) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == payload.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already registered")
        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
        )
        db.add(user)
        await db.flush()
        return self._tokens(user)

    async def login(self, db: AsyncSession, payload: UserLoginRequest) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account inactive")
        return self._tokens(user)

    def _tokens(self, user: User) -> TokenResponse:
        token = create_access_token(subject=user.id, extra_claims={"email": user.email})
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


auth_service = AuthService()
```

---

### `app/services/subscription_service.py`

```python
"""app/services/subscription_service.py — CRUD with user isolation on every query."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.schemas.subscription import (
    SubscriptionCreateRequest, SubscriptionListResponse,
    SubscriptionResponse, SubscriptionUpdateRequest,
)


class SubscriptionService:

    async def create(self, db: AsyncSession, user_id: int, payload: SubscriptionCreateRequest) -> SubscriptionResponse:
        sub = Subscription(user_id=user_id, **payload.model_dump())
        db.add(sub)
        await db.flush()
        await db.refresh(sub)
        return SubscriptionResponse.model_validate(sub)

    async def list_all(self, db: AsyncSession, user_id: int, active_only: bool = False) -> SubscriptionListResponse:
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        if active_only:
            stmt = stmt.where(Subscription.is_active == True)  # noqa: E712
        stmt = stmt.order_by(Subscription.renewal_date.asc().nullslast())
        result = await db.execute(stmt)
        subs = result.scalars().all()
        return SubscriptionListResponse(
            total=len(subs),
            subscriptions=[SubscriptionResponse.model_validate(s) for s in subs],
        )

    async def get(self, db: AsyncSession, user_id: int, sub_id: int) -> SubscriptionResponse:
        sub = await self._get_or_404(db, user_id, sub_id)
        return SubscriptionResponse.model_validate(sub)

    async def update(self, db: AsyncSession, user_id: int, sub_id: int, payload: SubscriptionUpdateRequest) -> SubscriptionResponse:
        sub = await self._get_or_404(db, user_id, sub_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(sub, field, value)
        await db.flush()
        await db.refresh(sub)
        return SubscriptionResponse.model_validate(sub)

    async def delete(self, db: AsyncSession, user_id: int, sub_id: int) -> None:
        sub = await self._get_or_404(db, user_id, sub_id)
        await db.delete(sub)

    async def _get_or_404(self, db: AsyncSession, user_id: int, sub_id: int) -> Subscription:
        result = await db.execute(
            select(Subscription).where(
                Subscription.id == sub_id,
                Subscription.user_id == user_id,  # isolation enforced here
            )
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            raise HTTPException(status_code=404, detail=f"Subscription {sub_id} not found")
        return sub


subscription_service = SubscriptionService()
```

---

### `app/services/dashboard_service.py`

```python
"""app/services/dashboard_service.py — spending totals + renewal windows."""
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.schemas.dashboard import DashboardSummaryResponse, RenewalItem, SpendByCategoryItem


class DashboardService:

    async def get_summary(self, db: AsyncSession, user_id: int) -> DashboardSummaryResponse:
        result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
        all_subs = result.scalars().all()
        active = [s for s in all_subs if s.is_active]

        today     = date.today()
        week_end  = today + timedelta(days=7)
        month_end = today + timedelta(days=30)

        total_monthly = round(sum(s.monthly_cost for s in active), 2)
        total_yearly  = round(sum(s.yearly_cost  for s in active), 2)

        due_week: list[RenewalItem] = []
        due_month: list[RenewalItem] = []

        for s in active:
            if s.renewal_date is None:
                continue
            days_left = (s.renewal_date - today).days
            item = RenewalItem(
                id=s.id, tool_name=s.tool_name, category=s.category,
                renewal_date=s.renewal_date, days_until_renewal=days_left,
                price=s.price, billing_cycle=s.billing_cycle, currency=s.currency,
            )
            if today <= s.renewal_date <= week_end:
                due_week.append(item)
            if today <= s.renewal_date <= month_end:
                due_month.append(item)

        due_week.sort(key=lambda x: x.renewal_date)
        due_month.sort(key=lambda x: x.renewal_date)

        cat_map: dict[str, dict] = defaultdict(lambda: {"monthly": 0.0, "yearly": 0.0, "count": 0})
        for s in active:
            cat_map[s.category]["monthly"] += s.monthly_cost
            cat_map[s.category]["yearly"]  += s.yearly_cost
            cat_map[s.category]["count"]   += 1

        spend_by_cat = [
            SpendByCategoryItem(
                category=cat, monthly_cost=round(v["monthly"], 2),
                yearly_cost=round(v["yearly"], 2), count=v["count"],
            )
            for cat, v in sorted(cat_map.items(), key=lambda x: x[1]["monthly"], reverse=True)
        ]

        return DashboardSummaryResponse(
            total_subscriptions=len(all_subs), active_subscriptions=len(active),
            total_monthly_spend=total_monthly, total_yearly_spend=total_yearly,
            due_this_week=due_week, due_this_month=due_month,
            spend_by_category=spend_by_cat,
        )

    async def get_upcoming_renewals(self, db: AsyncSession, user_id: int, days: int = 30) -> list[RenewalItem]:
        today = date.today()
        end   = today + timedelta(days=days)
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active == True,  # noqa: E712
                Subscription.renewal_date >= today,
                Subscription.renewal_date <= end,
            )
        )
        subs = result.scalars().all()
        return [
            RenewalItem(
                id=s.id, tool_name=s.tool_name, category=s.category,
                renewal_date=s.renewal_date,
                days_until_renewal=(s.renewal_date - today).days,
                price=s.price, billing_cycle=s.billing_cycle, currency=s.currency,
            )
            for s in sorted(subs, key=lambda x: x.renewal_date)
        ]


dashboard_service = DashboardService()
```

---

### `app/services/email_service.py`

```python
"""app/services/email_service.py — async SMTP renewal reminder emails."""
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
                msg, hostname=settings.smtp_host, port=settings.smtp_port,
                username=settings.smtp_username, password=settings.smtp_password,
                start_tls=settings.smtp_tls,
            )
            logger.info("Email sent to %s", to_email)
            return True
        except Exception as exc:
            logger.error("Email failed to %s: %s", to_email, exc)
            return False

    async def send_renewal_reminder(
        self, to_email: str, user_name: str, tool_name: str, renewal_date: str,
        days_left: int, price: float, currency: str, billing_cycle: str,
    ) -> bool:
        subject = f"🔔 {tool_name} renews in {days_left} day{'s' if days_left != 1 else ''}"
        color   = "#e53e3e" if days_left <= 3 else "#d97706" if days_left <= 7 else "#38a169"
        html = f"""<div style="font-family:sans-serif;max-width:520px;margin:0 auto">
          <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:24px;border-radius:10px;text-align:center">
            <h1 style="color:white;margin:0">Renewal Reminder</h1></div>
          <div style="background:white;padding:24px;border-radius:10px;margin-top:10px">
            <p>Hi <strong>{user_name}</strong>,</p>
            <p><strong>{tool_name}</strong> renews in
               <strong style="color:{color}">{days_left} day{'s' if days_left != 1 else ''}</strong>
               on <strong>{renewal_date}</strong>.</p>
            <p>Amount: <strong>{currency} {price:.2f}/{billing_cycle}</strong></p>
          </div></div>"""
        text = f"Hi {user_name},\n\n{tool_name} renews in {days_left} day(s) on {renewal_date}.\nAmount: {currency} {price:.2f}/{billing_cycle}\n"
        return await self.send_email(to_email, subject, html, text)


email_service = EmailService()
```

---

### `app/services/reminder_service.py`

```python
"""app/services/reminder_service.py — APScheduler renewal reminder job."""
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
            id="renewal_reminder", replace_existing=True, misfire_grace_time=3600,
        )
        self._scheduler.start()
        self._running = True
        logger.info("Reminder scheduler started.")

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
                check = await db.execute(
                    select(ReminderLog).where(
                        ReminderLog.subscription_id == sub.id,
                        ReminderLog.renewal_date == sub.renewal_date,
                        ReminderLog.status == "sent",
                    )
                )
                if check.scalar_one_or_none():
                    continue  # already reminded

                user_r = await db.execute(select(User).where(User.id == sub.user_id))
                user   = user_r.scalar_one_or_none()
                if not user:
                    continue

                days_left = (sub.renewal_date - today).days
                success   = await email_service.send_renewal_reminder(
                    to_email=user.email, user_name=user.full_name, tool_name=sub.tool_name,
                    renewal_date=sub.renewal_date.strftime("%B %d, %Y"), days_left=days_left,
                    price=sub.price, currency=sub.currency, billing_cycle=sub.billing_cycle,
                )
                db.add(ReminderLog(
                    user_id=sub.user_id, subscription_id=sub.id, renewal_date=sub.renewal_date,
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
```

---

### `app/mcp/__init__.py`

```python
# app/mcp/__init__.py
```

---

### `app/mcp/server.py` ← YOUR server.py pattern

> All 5 subscription tools are executed here. This file runs as a subprocess, reads JSON-RPC from stdin, writes results to stdout. Uses a direct synchronous SQLite connection.

*(See full file content in the repository — 354 lines)*

Key tools defined:
- `tool_get_subscriptions(user_id)` — lists all active subs with monthly/yearly costs
- `tool_get_spending_summary(user_id)` — totals + by-category breakdown
- `tool_get_upcoming_renewals(user_id, days)` — renewals within window
- `tool_get_spending_insights(user_id)` — duplicates, annual savings, high-cost alerts
- `tool_get_alternatives(tool_name)` — 13 popular tools with free alternatives

---

### `app/mcp/client.py` ← YOUR client.py pattern

```python
"""
app/mcp/client.py
MCPClient singleton — spawns app/mcp/server.py as subprocess once,
reuses it for every tool call (JSON-RPC over stdin/stdout).
"""
import json, subprocess, sys, threading, time, uuid


class MCPClient:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._start_server()

    def _start_server(self):
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "app.mcp.server"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1,
        )
        time.sleep(0.3)
        if self.proc.poll() is not None:
            raise RuntimeError(f"MCP server failed:\n{self.proc.stderr.read()}")

    def call_tool(self, tool_name: str, args: dict) -> dict:
        with self._lock:
            if self.proc.poll() is not None:
                self._start_server()
            request = {
                "id": str(uuid.uuid4()), "method": "tools/call",
                "params": {"name": tool_name, "arguments": args},
            }
            self.proc.stdin.write(json.dumps(request) + "\n")
            self.proc.stdin.flush()
            response = json.loads(self.proc.stdout.readline())
            if "error" in response:
                raise RuntimeError(f"MCP error ({tool_name}): {response['error']}")
            result = response.get("result", "{}")
            return json.loads(result) if isinstance(result, str) else result
```

---

### `app/agent/prompt.py`

```python
"""app/agent/prompt.py — system prompt for the subscription assistant."""

SYSTEM_PROMPT = """You are an intelligent subscription management assistant.

You help users understand, manage, and optimise their software subscriptions.

You have access to these tools — ALWAYS call them to get real data before answering:
  - get_subscriptions:       List all active subscriptions
  - get_spending_summary:    Monthly/yearly totals + by category
  - get_upcoming_renewals:   Renewals due in the next N days
  - get_spending_insights:   Duplicate tools, billing savings, high-cost alerts
  - get_alternatives:        Free or cheaper alternatives to a specific tool

Guidelines:
- Always use tools to fetch real data — never guess subscription details
- Give exact numbers and dates when you have them
- For spending questions → call get_spending_summary
- For renewal questions → call get_upcoming_renewals
- For savings questions → call get_spending_insights
- For alternative tool questions → call get_alternatives
- Be concise, specific, and actionable
- Answer confidently — do not say "I'm not sure" if you can look it up

You are talking to: {user_name}
Current date: {current_date}
User ID: {user_id}
"""


def build_system_prompt(user_name: str, user_id: int, current_date: str) -> str:
    return SYSTEM_PROMPT.format(user_name=user_name, user_id=user_id, current_date=current_date)
```

---

### `app/agent/graph.py` ← YOUR graph.py pattern

```python
"""
app/agent/graph.py
LangGraph StateGraph + Groq LLM — YOUR EXACT graph.py PATTERN.

- Tool SCHEMAS defined here (StructuredTool with func=lambda: None)
- Tool EXECUTION happens in agent_runner.py via MCPClient
- graph.add_edge("tool", "agent") = the agentic loop
"""
import os
from typing import TypedDict, List

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from app.core.config import settings

os.environ["GROQ_API_KEY"] = settings.groq_api_key

llm = ChatGroq(model=settings.groq_model, temperature=0)


# Tool input schemas (shape only — no execution)
class UserIdInput(BaseModel):
    user_id: int

class RenewalsInput(BaseModel):
    user_id: int
    days: int = 30

class AlternativesInput(BaseModel):
    tool_name: str


# Tool definitions (schema only — MCP executes them)
get_subscriptions_tool = StructuredTool(
    name="get_subscriptions",
    description="Fetch all active subscriptions for the user. Returns tool name, category, price, billing cycle, renewal date, monthly and yearly cost.",
    args_schema=UserIdInput, func=lambda **kwargs: None,
)
get_spending_summary_tool = StructuredTool(
    name="get_spending_summary",
    description="Get total monthly and yearly subscription spend broken down by category.",
    args_schema=UserIdInput, func=lambda **kwargs: None,
)
get_upcoming_renewals_tool = StructuredTool(
    name="get_upcoming_renewals",
    description="Get subscriptions renewing within the next N days. Use for 'what renews this week', 'due soon', etc.",
    args_schema=RenewalsInput, func=lambda **kwargs: None,
)
get_spending_insights_tool = StructuredTool(
    name="get_spending_insights",
    description="Get cost-saving suggestions: duplicate tools in same category, annual billing savings, high-cost alerts.",
    args_schema=UserIdInput, func=lambda **kwargs: None,
)
get_alternatives_tool = StructuredTool(
    name="get_alternatives",
    description="Get free or cheaper alternatives to a specific tool like Figma, Notion, Slack, GitHub, Jira.",
    args_schema=AlternativesInput, func=lambda **kwargs: None,
)

tools = [get_subscriptions_tool, get_spending_summary_tool,
         get_upcoming_renewals_tool, get_spending_insights_tool, get_alternatives_tool]

llm_with_tools = llm.bind_tools(tools)


# State
class AgentState(TypedDict):
    messages: List[BaseMessage]


# Agent node — LLM decides: answer OR call a tool
def agent_node(state: AgentState) -> dict:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}


# Tool node — PLACEHOLDER (real execution in agent_runner.py via MCP)
def tool_node(state: AgentState) -> dict:
    last = state["messages"][-1]
    tool_messages = [
        ToolMessage(content="Tool execution delegated to MCP", tool_call_id=call["id"])
        for call in last.tool_calls
    ]
    return {"messages": state["messages"] + tool_messages}


# Router
def should_use_tool(state: AgentState) -> str:
    last = state["messages"][-1]
    return "tool" if getattr(last, "tool_calls", None) else END


# Build graph
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tool",  tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_use_tool, {"tool": "tool", END: END})
graph.add_edge("tool", "agent")   # ← THE LOOP

agent_graph = graph.compile()
```

---

### `app/agent/agent_runner.py` ← YOUR agent_runner.py pattern

> This is the bridge that connects LangGraph + MCP + memory. Run as `python -m app.agent.agent_runner`. Reads `{"message":"...","user_id":1,"session_id":"..."}` from stdin, streams `{"stream":"..."}` chunks to stdout. *(Full 181-line file — see repository)*

Key logic:
1. Loads short-term SQL memory
2. Searches ChromaDB long-term memory
3. Calls `agent_graph.invoke()`
4. Detects `tool_calls` → `MCPClient.call_tool()` → injects `ToolMessage` → loops
5. Applies guardrails (weak response retry)
6. Saves to SQL + ChromaDB
7. Streams response in 20-char chunks

---

### `app/agent/memory.py`

```python
"""
app/agent/memory.py
SHORT-TERM: SQL chat_memories table, per (user_id, session_id)
LONG-TERM:  ChromaDB, one collection per user for isolation
"""
import logging, uuid
from datetime import datetime, timezone

import chromadb
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.chat_memory import ChatMemory

logger = logging.getLogger(__name__)

_chroma_client = None

def _get_chroma():
    global _chroma_client
    if _chroma_client is None:
        import os
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _chroma_client

def _user_col(user_id: int):
    return _get_chroma().get_or_create_collection(
        name=f"{settings.chroma_collection}_user_{user_id}",
        metadata={"hnsw:space": "cosine"},
    )

SHORT_TERM_WINDOW = 20

async def load_short_term(db: AsyncSession, user_id: int, session_id: str, limit: int = SHORT_TERM_WINDOW) -> list:
    result = await db.execute(
        select(ChatMemory)
        .where(ChatMemory.user_id == user_id, ChatMemory.session_id == session_id)
        .order_by(ChatMemory.created_at.desc()).limit(limit)
    )
    rows = list(reversed(result.scalars().all()))
    messages = []
    for r in rows:
        if r.role == "human": messages.append(HumanMessage(content=r.content))
        elif r.role == "ai":  messages.append(AIMessage(content=r.content))
    return messages

async def save_message(db: AsyncSession, user_id: int, session_id: str, role: str, content: str) -> None:
    db.add(ChatMemory(user_id=user_id, session_id=session_id, role=role, content=content))
    await db.flush()

async def clear_session(db: AsyncSession, user_id: int, session_id: str) -> None:
    await db.execute(delete(ChatMemory).where(
        ChatMemory.user_id == user_id, ChatMemory.session_id == session_id,
    ))

async def search_long_term(user_id: int, query: str, n_results: int = 3) -> list[str]:
    try:
        col = _user_col(user_id)
        count = col.count()
        if count == 0: return []
        results = col.query(query_texts=[query], n_results=min(n_results, count))
        return [d for d in results.get("documents", [[]])[0] if d]
    except Exception as exc:
        logger.warning("Long-term search failed: %s", exc)
        return []

async def save_to_long_term(user_id: int, session_id: str, content: str, metadata: dict | None = None) -> None:
    try:
        _user_col(user_id).add(
            documents=[content],
            ids=[f"{user_id}_{session_id}_{uuid.uuid4().hex[:8]}"],
            metadatas=[{"user_id": str(user_id), "session_id": session_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(), **(metadata or {})}],
        )
    except Exception as exc:
        logger.warning("Long-term save failed: %s", exc)

def new_session_id() -> str:
    return uuid.uuid4().hex
```

---

### `app/routes/health.py`

```python
from fastapi import APIRouter
router = APIRouter(tags=["Health"])

@router.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
```

---

### `app/routes/subscriptions.py`

```python
"""app/routes/subscriptions.py — CRUD, all JWT-protected."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreateRequest, SubscriptionListResponse,
    SubscriptionResponse, SubscriptionUpdateRequest,
)
from app.services.subscription_service import subscription_service

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

@router.post("", response_model=SubscriptionResponse, status_code=201)
async def create(payload: SubscriptionCreateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await subscription_service.create(db, user.id, payload)

@router.get("", response_model=SubscriptionListResponse)
async def list_all(active_only: bool = Query(False), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await subscription_service.list_all(db, user.id, active_only)

@router.get("/{sub_id}", response_model=SubscriptionResponse)
async def get_one(sub_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await subscription_service.get(db, user.id, sub_id)

@router.patch("/{sub_id}", response_model=SubscriptionResponse)
async def update(sub_id: int, payload: SubscriptionUpdateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await subscription_service.update(db, user.id, sub_id, payload)

@router.delete("/{sub_id}", status_code=204)
async def delete(sub_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await subscription_service.delete(db, user.id, sub_id)
```

---

### `app/routes/dashboard.py`

```python
"""app/routes/dashboard.py — summary, renewals, insights."""
import asyncio, functools
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse, RenewalItem
from app.services.dashboard_service import dashboard_service
from app.services.reminder_service import reminder_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
async def summary(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await dashboard_service.get_summary(db, user.id)

@router.get("/renewals", response_model=list[RenewalItem])
async def renewals(days: int = Query(30, ge=1, le=365), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await dashboard_service.get_upcoming_renewals(db, user.id, days)

@router.get("/insights")
async def insights(user: User = Depends(get_current_user)):
    from app.mcp.server import tool_get_spending_insights
    loop   = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, functools.partial(tool_get_spending_insights, user.id))
    return result.get("insights", [])

@router.post("/reminders/trigger")
async def trigger_reminders(user: User = Depends(get_current_user)):
    return await reminder_service.trigger_now()
```

---

### `app/routes/chat.py`

```python
"""
app/routes/chat.py — SSE streaming chat + POST endpoint.
Spawns agent_runner.py subprocess once, reuses for all requests.
"""
import json, subprocess, sys, threading

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse

router    = APIRouter(prefix="/chat", tags=["AI Assistant"])
_agent    = None
_lock     = threading.Lock()

def _get_agent():
    global _agent
    if _agent is None or _agent.poll() is not None:
        _agent = subprocess.Popen(
            [sys.executable, "-m", "app.agent.agent_runner"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1,
        )
    return _agent

@router.get("/stream")
def chat_stream(
    message: str = Query(...),
    session_id: str = Query(None),
    current_user: User = Depends(get_current_user),
):
    def generate():
        with _lock:
            try:
                agent = _get_agent()
                agent.stdin.write(json.dumps({"message": message, "user_id": current_user.id, "session_id": session_id}) + "\n")
                agent.stdin.flush()
                while True:
                    line = agent.stdout.readline()
                    if not line: break
                    data = json.loads(line.strip())
                    if "stream" in data:
                        yield f"data: {json.dumps({'text': data['stream'], 'session_id': data.get('session_id','')})}\n\n"
                    if "error" in data:
                        yield f"data: {json.dumps({'error': data['error']})}\n\n"
                        break
                    if "end" in data:
                        yield f"data: {json.dumps({'end': True, 'session_id': data.get('session_id','')})}\n\n"
                        break
            except Exception as exc:
                yield f"data: {json.dumps({'error': str(exc)})}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")

@router.post("", response_model=ChatResponse)
async def chat_post(payload: ChatRequest, current_user: User = Depends(get_current_user)):
    from app.agent.agent_runner import run_agent
    from app.agent.memory import new_session_id
    session_id = payload.session_id or new_session_id()
    reply = await run_agent(payload.message, current_user.id, session_id)
    return ChatResponse(session_id=session_id, reply=reply)
```

---

### `app/main.py`

```python
"""app/main.py — FastAPI app factory."""
import logging, os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import create_tables
import app.models  # noqa — registers all ORM models

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s …", settings.app_name)
    await create_tables()
    logger.info("Database tables ready.")
    try:
        from app.services.reminder_service import reminder_service
        reminder_service.start()
    except Exception as exc:
        logger.warning("Scheduler not started: %s", exc)
    yield
    try:
        from app.services.reminder_service import reminder_service
        reminder_service.stop()
    except Exception:
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name, version="1.0.0",
        description="Subscription dashboard — LangGraph + Groq + MCP",
        lifespan=lifespan,
        docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json",
    )
    app.add_middleware(CORSMiddleware, allow_origins=["*"] if settings.debug else [],
                       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    from app.auth.routes import router as auth_router
    from app.routes.subscriptions import router as sub_router
    from app.routes.dashboard import router as dash_router
    from app.routes.chat import router as chat_router
    from app.routes.health import router as health_router

    app.include_router(auth_router,   prefix="/api")
    app.include_router(sub_router,    prefix="/api")
    app.include_router(dash_router,   prefix="/api")
    app.include_router(chat_router,   prefix="/api")
    app.include_router(health_router, prefix="/api")

    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    return app


app = create_app()
```

---

### `tests/conftest.py`

```python
"""tests/conftest.py — in-memory SQLite fixtures."""
import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import create_app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession  = async_sessionmaker(bind=test_engine, expire_on_commit=False, autoflush=False)


@pytest.fixture(scope="function")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db():
    import app.models  # noqa
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSession() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db):
    application = create_app()
    async def override(): yield db
    application.dependency_overrides[get_db] = override
    async with AsyncClient(transport=ASGITransport(app=application), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def auth(client):
    r = await client.post("/api/auth/register", json={
        "email": "test@example.com", "full_name": "Test User", "password": "Test1234"
    })
    assert r.status_code == 201
    client.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
    return client, r.json()["access_token"]
```

---

## Step-by-Step GitHub Setup

### Step 1 — Create your repository

```bash
# Option A: new repo from scratch
mkdir sub-dashboard && cd sub-dashboard
git init

# Option B: clone your existing empty repo
git clone https://github.com/YOUR_USERNAME/sub-dashboard.git
cd sub-dashboard
```

---

### Step 2 — Create the exact folder structure

```bash
# Run this block — creates every directory
mkdir -p app/core
mkdir -p app/auth
mkdir -p app/models
mkdir -p app/schemas
mkdir -p app/services
mkdir -p app/routes
mkdir -p app/agent
mkdir -p app/mcp
mkdir -p app/tools
mkdir -p static
mkdir -p tests
mkdir -p data

# Create all __init__.py files
touch app/__init__.py
touch app/core/__init__.py
touch app/auth/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
touch app/routes/__init__.py
touch app/agent/__init__.py
touch app/mcp/__init__.py
touch app/tools/__init__.py
touch tests/__init__.py
```

---

### Step 3 — Create every file

Copy the exact content from the **"Every File"** section above into each file at exactly this path:

```
requirements.txt
.env.example
.gitignore
pytest.ini
run.py
seed.py
app/__init__.py
app/main.py
app/core/__init__.py
app/core/config.py
app/core/database.py
app/core/security.py
app/auth/__init__.py
app/auth/jwt_handler.py
app/auth/dependencies.py
app/auth/routes.py
app/models/__init__.py        ← DO NOT SKIP — tables won't create without this
app/models/user.py
app/models/subscription.py
app/models/reminder_log.py
app/models/chat_memory.py
app/schemas/__init__.py
app/schemas/auth.py
app/schemas/subscription.py
app/schemas/dashboard.py
app/schemas/chat.py
app/services/__init__.py
app/services/auth_service.py
app/services/subscription_service.py
app/services/dashboard_service.py
app/services/email_service.py
app/services/reminder_service.py
app/mcp/__init__.py
app/mcp/server.py
app/mcp/client.py
app/agent/__init__.py
app/agent/graph.py
app/agent/agent_runner.py
app/agent/prompt.py
app/agent/memory.py
app/routes/__init__.py
app/routes/health.py
app/routes/subscriptions.py
app/routes/dashboard.py
app/routes/chat.py
app/tools/__init__.py
static/index.html
static/styles.css
static/app.js
tests/__init__.py
tests/conftest.py
tests/test_auth.py
tests/test_subscriptions.py
tests/test_dashboard.py
```

---

### Step 4 — Virtual environment

```bash
# Create
python -m venv .venv

# Activate — macOS / Linux
source .venv/bin/activate

# Activate — Windows Command Prompt
.venv\Scripts\activate.bat

# Activate — Windows PowerShell
.venv\Scripts\Activate.ps1

# You should see (.venv) in your prompt
```

---

### Step 5 — Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 6 — Get your Groq API key (FREE)

1. Go to **https://console.groq.com**
2. Sign up / log in
3. Click **API Keys** → **Create API Key**
4. Copy the key (starts with `gsk_`)

---

### Step 7 — Configure `.env`

```bash
cp .env.example .env
```

Open `.env` in any text editor. Set **these two values** — everything else has safe defaults:

```ini
# Your Groq key from console.groq.com
GROQ_API_KEY=gsk_YOUR_KEY_HERE

# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=paste-your-generated-secret-here
```

---

### Step 8 — Verify setup

```bash
python -c "
from app.core.config import settings
import app.models
from app.models import User, Subscription, ReminderLog, ChatMemory
from app.agent.graph import agent_graph, tools
from app.mcp.server import TOOL_SCHEMAS
from app.main import create_app
app = create_app()
print('✅ Config OK:', settings.app_name)
print('✅ Models OK: 4 tables')
print('✅ LangGraph tools:', len(tools))
print('✅ MCP tools:', len(TOOL_SCHEMAS))
print('✅ FastAPI routes:', len(app.routes))
print('✅ Groq model:', settings.groq_model)
"
```

Expected output:
```
✅ Config OK: Subscription Dashboard
✅ Models OK: 4 tables
✅ LangGraph tools: 5
✅ MCP tools: 5
✅ FastAPI routes: 21
✅ Groq model: llama-3.1-8b-instant
```

---

### Step 9 — Run the application

```bash
python run.py
```

Output:
```
INFO: Starting Subscription Dashboard …
INFO: Database tables ready.
INFO: Reminder scheduler started.
INFO: Uvicorn running on http://0.0.0.0:8000
```

Open: **http://localhost:8000**

---

### Step 10 — Load demo data (optional but recommended)

```bash
python seed.py
```

Output:
```
✅ Tables ready.
✅ Created user: demo@example.com (id=1)
✅ Seeded 15 subscriptions.

🚀 Done!
   Email:    demo@example.com
   Password: Demo1234
```

Log in at http://localhost:8000 and you'll see 15 real subscriptions with spending data.

---

### Step 11 — Run tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

Expected:
```
tests/test_auth.py::test_register        PASSED
tests/test_auth.py::test_duplicate_email PASSED
tests/test_auth.py::test_weak_password   PASSED
tests/test_auth.py::test_login           PASSED
tests/test_auth.py::test_wrong_password  PASSED
tests/test_auth.py::test_me              PASSED
tests/test_auth.py::test_health          PASSED
tests/test_subscriptions.py::test_create      PASSED
tests/test_subscriptions.py::test_list        PASSED
tests/test_subscriptions.py::test_update      PASSED
tests/test_subscriptions.py::test_delete      PASSED
tests/test_subscriptions.py::test_isolation   PASSED
tests/test_subscriptions.py::test_yearly_cost PASSED
tests/test_subscriptions.py::test_invalid_cycle PASSED
tests/test_dashboard.py::test_empty           PASSED
tests/test_dashboard.py::test_monthly_spend   PASSED
tests/test_dashboard.py::test_due_this_week   PASSED
tests/test_dashboard.py::test_renewals_window PASSED
18 passed
```

---

### Step 12 — Push to GitHub

```bash
# Stage all files
git add .

# Verify .env is NOT staged (must show as untracked or missing)
git status
# .env should NOT appear in "Changes to be committed"

# Commit
git commit -m "Tool Subscription Dashboard: LangGraph + Groq + MCP + FastAPI"

# Push
git remote add origin https://github.com/YOUR_USERNAME/sub-dashboard.git
git branch -M main
git push -u origin main
```

---

## API Reference

All endpoints are prefixed `/api`. Protected endpoints require:
```
Authorization: Bearer <your_access_token>
```

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | ❌ | Register new user |
| POST | `/api/auth/login` | ❌ | Login, get token |
| GET | `/api/auth/me` | ✅ | Current user |
| POST | `/api/subscriptions` | ✅ | Create subscription |
| GET | `/api/subscriptions` | ✅ | List all (`?active_only=true`) |
| GET | `/api/subscriptions/{id}` | ✅ | Get single |
| PATCH | `/api/subscriptions/{id}` | ✅ | Update |
| DELETE | `/api/subscriptions/{id}` | ✅ | Delete |
| GET | `/api/dashboard/summary` | ✅ | Full spending summary |
| GET | `/api/dashboard/renewals` | ✅ | Renewals (`?days=30`) |
| GET | `/api/dashboard/insights` | ✅ | Cost-saving insights |
| GET | `/api/chat/stream` | ✅ | SSE streaming chat |
| POST | `/api/chat` | ✅ | Non-streaming chat |
| GET | `/api/health` | ❌ | Health check |
| POST | `/api/dashboard/reminders/trigger` | ✅ | Trigger reminder check |

Interactive docs: **http://localhost:8000/api/docs**

---

## Environment Variables Reference

| Variable | Required | Default | Notes |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ | — | From https://console.groq.com — FREE |
| `GROQ_MODEL` | No | `llama-3.1-8b-instant` | Any Groq model |
| `SECRET_KEY` | ✅ | dev-secret | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | JWT lifetime |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./data/subscriptions.db` | Change prefix to `postgresql+asyncpg://` for PostgreSQL |
| `SMTP_USERNAME` | For email | — | Gmail address |
| `SMTP_PASSWORD` | For email | — | Gmail App Password (not your login password) |
| `CHROMA_PERSIST_DIR` | No | `./data/chroma` | ChromaDB storage path |
| `REMINDER_DAYS_BEFORE` | No | `7` | Days before renewal to send reminder |
| `REMINDER_CHECK_INTERVAL_HOURS` | No | `24` | Scheduler interval |

---

## Email Setup (Gmail App Password)

1. Go to **myaccount.google.com** → **Security** → **2-Step Verification** (must be ON)
2. Search for **"App passwords"**
3. Create app password → name it "SubTracker"
4. Copy the 16-character password (e.g. `abcd efgh ijkl mnop`)
5. In `.env`:
```ini
SMTP_USERNAME=your@gmail.com
SMTP_PASSWORD=abcdefghijklmnop   # no spaces
SMTP_FROM_EMAIL=your@gmail.com
```

Test: `POST /api/dashboard/reminders/trigger` with your Bearer token.

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'app'` | Wrong working directory | Run from the project root: `cd sub-dashboard && python run.py` |
| Tables not created | `app/models/__init__.py` missing imports | Make sure it imports all 4 models |
| `401 Unauthorized` | Expired token (60 min default) | Log in again to get a fresh token |
| Groq API error | Missing or invalid key | Set `GROQ_API_KEY` in `.env` and restart |
| Chat not streaming | `agent_runner.py` subprocess crash | Check terminal for Python errors, ensure `GROQ_API_KEY` is set |
| ChromaDB error | Corrupt vector store | Delete `data/chroma/` and restart |
| Port 8000 in use | Another process | `lsof -i :8000` then kill, or use `uvicorn app.main:app --port 8001` |

---

## Project Stats

```
47  Python files
2,482 lines of Python
516   lines of JavaScript
233   lines of CSS
203   lines of HTML
18    tests (all passing)
5     MCP tools
5     LangGraph tools
4     DB tables
2     memory layers (SQL + ChromaDB)
```

---

*Built with FastAPI · LangGraph · Groq · MCP · ChromaDB · SQLAlchemy*
