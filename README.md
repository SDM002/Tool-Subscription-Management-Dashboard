# 📦 Tool Subscription Management Dashboard

> A full-stack web application to manage your software subscriptions with an AI-powered assistant, automated email reminders, and detailed spending insights.

---

## Table of Contents

1. [What This Project Does](#what-this-project-does)
2. [Tech Stack](#tech-stack)
3. [Complete Folder Structure](#complete-folder-structure)
4. [Every File Explained](#every-file-explained)
5. [How The Files Connect](#how-the-files-connect)
6. [Prerequisites](#prerequisites)
7. [Step-by-Step Setup on Your Machine](#step-by-step-setup-on-your-machine)
8. [Environment Variables Reference](#environment-variables-reference)
9. [Running the App](#running-the-app)
10. [Seeding Demo Data](#seeding-demo-data)
11. [API Reference](#api-reference)
12. [Running Tests](#running-tests)
13. [Manual Testing Checklist](#manual-testing-checklist)
14. [Pushing to GitHub](#pushing-to-github)
15. [Troubleshooting](#troubleshooting)
16. [Future Enhancements](#future-enhancements)

---

## What This Project Does

| Feature | Description |
|---|---|
| 🔐 Auth | JWT-based register / login. Passwords hashed with bcrypt |
| 📋 CRUD | Add, edit, delete, view subscriptions per user |
| 📊 Dashboard | Monthly spend, yearly spend, due-soon renewals, category breakdown |
| 🔔 Reminders | APScheduler sends email reminders N days before renewal via SMTP |
| 🤖 AI Assistant | Claude-powered chat with tool/function calling |
| 🧠 Short-term memory | Last 20 messages stored in SQLite per session |
| 💾 Long-term memory | ChromaDB vector store for semantic retrieval across sessions |
| 💡 Insights | Duplicate tool detection, annual billing savings, high-cost alerts |
| 🔒 Isolation | Every query is scoped to user_id — users never see each other's data |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI (async) |
| Database | SQLite (via aiosqlite) — swap to PostgreSQL by changing one env var |
| ORM | SQLAlchemy 2.0 (async) |
| Validation | Pydantic v2 |
| Authentication | JWT (python-jose) + bcrypt (passlib) |
| Scheduler | APScheduler (AsyncIOScheduler) |
| Email | aiosmtplib (async SMTP) |
| LLM | Anthropic Claude (claude-sonnet-4-20250514) |
| Long-term memory | ChromaDB (persistent vector store) |
| Frontend | Vanilla HTML + CSS + JavaScript (no build step) |

---

## Complete Folder Structure

```
tool-subscription-dashboard/
│
├── app/                          ← All backend Python code
│   ├── __init__.py
│   ├── main.py                   ← FastAPI app factory + startup
│   │
│   ├── core/                     ← Shared foundation
│   │   ├── __init__.py
│   │   ├── config.py             ← All settings from .env
│   │   ├── database.py           ← SQLAlchemy engine + session
│   │   └── security.py           ← Password hash/verify
│   │
│   ├── auth/                     ← Authentication layer
│   │   ├── __init__.py
│   │   ├── jwt_handler.py        ← Create/decode JWT tokens
│   │   ├── dependencies.py       ← get_current_user FastAPI dep
│   │   └── routes.py             ← /auth/register, /auth/login, /auth/me
│   │
│   ├── models/                   ← SQLAlchemy ORM models (DB tables)
│   │   ├── __init__.py           ← Imports all models (required for create_tables)
│   │   ├── user.py               ← users table
│   │   ├── subscription.py       ← subscriptions table
│   │   ├── reminder_log.py       ← reminder_logs table
│   │   └── chat_memory.py        ← chat_memories table
│   │
│   ├── schemas/                  ← Pydantic request/response shapes
│   │   ├── __init__.py
│   │   ├── auth.py               ← Register/login req + token resp
│   │   ├── subscription.py       ← Create/update/response for subs
│   │   ├── dashboard.py          ← Dashboard summary + renewal items
│   │   └── chat.py               ← Chat request/response
│   │
│   ├── services/                 ← Business logic (called by routes)
│   │   ├── __init__.py
│   │   ├── auth_service.py       ← Register + login logic
│   │   ├── subscription_service.py ← CRUD with user isolation
│   │   ├── dashboard_service.py  ← Spending totals + renewal lists
│   │   ├── pricing_service.py    ← Cost-saving insight rules
│   │   ├── email_service.py      ← SMTP email sender
│   │   └── reminder_service.py   ← APScheduler + reminder job
│   │
│   ├── routes/                   ← FastAPI route handlers (thin layer)
│   │   ├── __init__.py
│   │   ├── health.py             ← GET /api/health
│   │   ├── subscriptions.py      ← CRUD /api/subscriptions
│   │   ├── dashboard.py          ← /api/dashboard/summary|renewals|insights
│   │   └── chat.py               ← /api/chat (AI assistant)
│   │
│   ├── agent/                    ← AI assistant components
│   │   ├── __init__.py
│   │   ├── prompt.py             ← System prompt template
│   │   ├── memory.py             ← Short-term (SQL) + long-term (ChromaDB)
│   │   ├── tools_registry.py     ← Tool schemas + dispatcher for Claude
│   │   └── assistant_service.py  ← Core chat loop with tool calling
│   │
│   └── tools/                    ← Tool implementations called by agent
│       ├── __init__.py
│       ├── spend_analysis.py     ← get_subscriptions, get_spending_summary
│       ├── renewal_analysis.py   ← get_upcoming_renewals
│       ├── recommendation_tool.py ← get_spending_insights
│       └── alternative_lookup.py ← Static DB of cheaper alternatives
│
├── static/                       ← Frontend (served by FastAPI)
│   ├── index.html                ← Single-page app shell
│   ├── styles.css                ← Complete design system
│   └── app.js                    ← All frontend logic
│
├── tests/                        ← Pytest test suite
│   ├── __init__.py
│   ├── conftest.py               ← Shared fixtures (in-memory DB, test client)
│   ├── test_auth.py              ← Register, login, /me tests
│   ├── test_subscriptions.py     ← CRUD + isolation tests
│   └── test_dashboard.py         ← Metrics + insights tests
│
├── data/                         ← Created automatically at runtime
│   ├── subscriptions.db          ← SQLite database file
│   └── chroma/                   ← ChromaDB vector store files
│
├── .env                          ← Your local secrets (never commit this)
├── .env.example                  ← Template with all keys (safe to commit)
├── .gitignore                    ← Excludes .env, data/, __pycache__, etc.
├── requirements.txt              ← All Python dependencies
├── run.py                        ← Entry point: python run.py
├── seed.py                       ← Populate DB with demo data
└── README.md                     ← This file
```

---

## Every File Explained

### `app/core/config.py`
Reads all environment variables from `.env` using `pydantic-settings`. Every other module imports `settings` from here — there are no scattered `os.getenv()` calls. If a key is missing it uses a safe default.

### `app/core/database.py`
Creates the async SQLAlchemy engine and session factory. Provides:
- `get_db()` — FastAPI dependency, yields a session per request, auto-commits or rolls back
- `get_db_context()` — async context manager for background jobs (scheduler)
- `create_tables()` — called at startup to create all tables

### `app/core/security.py`
Two functions only: `hash_password()` and `verify_password()` using bcrypt.

### `app/auth/jwt_handler.py`
`create_access_token()`, `create_refresh_token()`, `decode_token()`. Uses python-jose. Tokens carry `sub` (user id) and `type` (access|refresh).

### `app/auth/dependencies.py`
`get_current_user()` — the FastAPI dependency every protected route uses. Reads `Authorization: Bearer <token>`, decodes it, fetches the user from DB, raises 401 if anything is wrong.

### `app/auth/routes.py`
Four endpoints: `POST /register`, `POST /login`, `GET /me`, `POST /logout`. Thin — all logic is in `auth_service`.

### `app/models/*.py`
ORM table definitions. `models/__init__.py` imports all four models so SQLAlchemy's metadata knows about them before `create_tables()` runs. **This import is critical** — without it, tables won't be created.

### `app/schemas/*.py`
Pydantic v2 models. Separate schemas for requests vs responses. ORM models are never returned directly from routes — they always go through a schema with `model_validate()`.

### `app/services/subscription_service.py`
All five CRUD operations. Every query has `Subscription.user_id == user_id` — this is the data isolation guarantee. If a user tries to access another user's subscription, they get 404.

### `app/services/dashboard_service.py`
Calculates totals by summing `monthly_cost` / `yearly_cost` properties on each Subscription. Groups renewals by 7-day and 30-day windows. Groups spend by category.

### `app/services/pricing_service.py`
Pure Python rules engine — no LLM needed. Detects: multiple tools in same category (duplicates), monthly subs where switching to annual saves ~17%, subscriptions costing over $50/month.

### `app/services/email_service.py`
Async SMTP via `aiosmtplib`. Builds a styled HTML email for renewal reminders. If SMTP credentials are not configured, logs a warning and returns False instead of crashing.

### `app/services/reminder_service.py`
`AsyncIOScheduler` runs `_check_and_send_reminders()` every N hours. Queries subscriptions renewing within `REMINDER_DAYS_BEFORE` days. Checks `reminder_logs` to avoid duplicate sends. Logs each send attempt.

### `app/agent/assistant_service.py`
The core AI loop. On each message:
1. Loads short-term SQL history for the session
2. Searches ChromaDB for relevant past context
3. Calls Claude with tool definitions
4. If Claude returns `tool_use` blocks, dispatches tools, appends results, calls Claude again
5. Repeats up to 5 times until `end_turn`
6. Saves exchange to both SQL and ChromaDB

### `app/agent/memory.py`
- **Short-term**: `load_short_term()` / `save_message()` — SQL chat_memories table, scoped per (user_id, session_id)
- **Long-term**: `search_long_term()` / `save_to_long_term()` — ChromaDB, one collection per user (`subscription_memory_user_<id>`)

### `app/agent/tools_registry.py`
Two responsibilities:
1. `TOOL_DEFINITIONS` — the JSON schemas Claude sees to know what tools exist
2. `dispatch_tool()` — receives `(tool_name, tool_input)` from Claude and calls the right Python function

### `app/tools/*.py`
Each file is one tool implementation. They take `(db, user_id)` and return a plain dict that gets JSON-serialised back to Claude.

### `static/index.html`
Single HTML file. Contains the auth page (login/register), sidebar navigation, and five page sections (dashboard, subscriptions, renewals, insights, chat). Everything is shown/hidden by JavaScript.

### `static/app.js`
~600 lines of vanilla JavaScript. Contains:
- `apiFetch()` — wrapper around fetch() that attaches the JWT header and handles 401
- Auth handlers, page router, all page renderers
- Subscription modal (add/edit/delete)
- Chat UI with typing indicator, suggestion chips, auto-scroll

### `static/styles.css`
Full design system with CSS variables. No external dependencies. Responsive down to mobile.

### `seed.py`
Creates a demo user + 15 realistic subscriptions. Safe to run multiple times (skips if user exists).

### `tests/conftest.py`
Uses an in-memory SQLite database so tests never touch your real data. Provides `client` (unauthenticated) and `auth_client` (pre-logged-in) fixtures.

---

## How The Files Connect

```
HTTP Request
     │
     ▼
app/main.py              ← registers all routers, mounts static files
     │
     ▼
app/routes/*.py          ← thin handlers, use Depends(get_current_user)
     │                                                    │
     │                                         app/auth/dependencies.py
     │                                                    │
     │                                         app/auth/jwt_handler.py
     │
     ▼
app/services/*.py        ← all business logic lives here
     │
     ├── app/core/database.py    ← AsyncSession
     ├── app/models/*.py         ← ORM queries
     └── app/schemas/*.py        ← input validation + output shaping

app/agent/assistant_service.py
     │
     ├── app/agent/memory.py         ← SQL short-term + ChromaDB long-term
     ├── app/agent/prompt.py         ← system prompt
     ├── app/agent/tools_registry.py ← tool definitions + dispatcher
     └── app/tools/*.py              ← actual tool implementations
              │
              └── app/services/*.py  ← tools reuse service layer

app/services/reminder_service.py
     │
     ├── APScheduler (background thread)
     ├── app/services/email_service.py
     └── app/core/database.get_db_context()  ← no FastAPI dep injection here

static/index.html + app.js + styles.css
     │
     └── all API calls go to /api/* endpoints above
```

---

## Prerequisites

Before you start, make sure you have:

| Tool | Version | Check command |
|---|---|---|
| Python | 3.11 or 3.12 | `python --version` |
| pip | latest | `pip --version` |
| git | any recent | `git --version` |
| Anthropic API key | — | Get at https://console.anthropic.com |
| Gmail app password (optional) | — | For email reminders |

---

## Step-by-Step Setup on Your Machine

### Step 1 — Clone or create the repository

If you are starting fresh on GitHub:

```bash
# Option A: You already have a GitHub repo — clone it
git clone https://github.com/YOUR_USERNAME/tool-subscription-dashboard.git
cd tool-subscription-dashboard

# Option B: Create a new local project and push later
mkdir tool-subscription-dashboard
cd tool-subscription-dashboard
git init
```

### Step 2 — Create the exact folder structure

Run these commands inside your project root:

```bash
# Create all directories
mkdir -p app/core
mkdir -p app/auth
mkdir -p app/models
mkdir -p app/schemas
mkdir -p app/services
mkdir -p app/routes
mkdir -p app/agent
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
touch app/tools/__init__.py
touch tests/__init__.py
```

### Step 3 — Copy all project files

Create every file listed in the folder structure above. The content for each file is in this repository. See the [Every File Explained](#every-file-explained) section for what each file does.

**Critical files that must exist (in order of importance):**
```
requirements.txt
.env.example
.gitignore
run.py
seed.py
app/__init__.py
app/main.py
app/core/config.py
app/core/database.py
app/core/security.py
app/auth/jwt_handler.py
app/auth/dependencies.py
app/auth/routes.py
app/models/__init__.py        ← MUST import all 4 models
app/models/user.py
app/models/subscription.py
app/models/reminder_log.py
app/models/chat_memory.py
app/schemas/auth.py
app/schemas/subscription.py
app/schemas/dashboard.py
app/schemas/chat.py
app/services/auth_service.py
app/services/subscription_service.py
app/services/dashboard_service.py
app/services/pricing_service.py
app/services/email_service.py
app/services/reminder_service.py
app/routes/health.py
app/routes/subscriptions.py
app/routes/dashboard.py
app/routes/chat.py
app/agent/prompt.py
app/agent/memory.py
app/agent/tools_registry.py
app/agent/assistant_service.py
app/tools/spend_analysis.py
app/tools/renewal_analysis.py
app/tools/recommendation_tool.py
app/tools/alternative_lookup.py
static/index.html
static/styles.css
static/app.js
tests/conftest.py
tests/test_auth.py
tests/test_subscriptions.py
tests/test_dashboard.py
```

### Step 4 — Create a Python virtual environment

```bash
# Create virtual environment (do this once)
python -m venv .venv

# Activate it — macOS/Linux:
source .venv/bin/activate

# Activate it — Windows (Command Prompt):
.venv\Scripts\activate.bat

# Activate it — Windows (PowerShell):
.venv\Scripts\Activate.ps1

# You should now see (.venv) in your terminal prompt
```

### Step 5 — Install all dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs everything: FastAPI, SQLAlchemy, Pydantic, JWT, bcrypt, APScheduler, aiosmtplib, Anthropic, ChromaDB, and all their dependencies.

**Expected output:** Many lines of `Installing ...`, ending with `Successfully installed ...`

### Step 6 — Create your `.env` file

```bash
# Copy the example file
cp .env.example .env
```

Now open `.env` in any text editor and fill in:

```ini
# REQUIRED — generate a real secret:
# Run: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=paste-your-generated-secret-here

# REQUIRED for AI assistant
ANTHROPIC_API_KEY=sk-ant-api03-...

# OPTIONAL — fill in for email reminders (see Email Setup below)
SMTP_USERNAME=your-gmail@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Leave everything else as default for local development
```

### Step 7 — Verify the setup

```bash
python -c "
from app.core.config import settings
from app.models import User, Subscription, ReminderLog, ChatMemory
print('✅ Config loaded:', settings.app_name)
print('✅ Models imported OK')
print('✅ DB URL:', settings.database_url)
"
```

Expected output:
```
✅ Config loaded: Tool Subscription Dashboard
✅ Models imported OK
✅ DB URL: sqlite+aiosqlite:///./data/subscriptions.db
```

### Step 8 — Run the application

```bash
python run.py
```

You will see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Starting up Tool Subscription Dashboard …
INFO:     Database tables ready.
INFO:     Reminder scheduler started.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Open your browser: **http://localhost:8000**

---

## Email Setup (Gmail)

To enable email reminders:

1. Go to your Google Account → **Security** → **2-Step Verification** (must be ON)
2. Go to **Security** → **App passwords**
3. Create a new app password for "Mail" / "Other (custom name)" → name it "SubTracker"
4. Copy the 16-character password shown (e.g. `abcd efgh ijkl mnop`)
5. In your `.env`:
   ```ini
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-gmail@gmail.com
   SMTP_PASSWORD=abcdefghijklmnop    # no spaces
   SMTP_FROM_EMAIL=your-gmail@gmail.com
   SMTP_TLS=true
   ```

To test immediately without waiting for the scheduler:
```bash
# After starting the app, call the manual trigger endpoint:
curl -X POST http://localhost:8000/api/admin/reminders/trigger \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ YES | dev-secret-change-me | JWT signing secret. Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ALGORITHM` | no | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | 60 | JWT access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | no | 7 | JWT refresh token lifetime |
| `DATABASE_URL` | no | sqlite+aiosqlite:///./data/subscriptions.db | SQLite by default. Change to `postgresql+asyncpg://user:pass@host/db` for PostgreSQL |
| `ANTHROPIC_API_KEY` | ✅ for AI | — | Get from https://console.anthropic.com |
| `LLM_MODEL` | no | claude-sonnet-4-20250514 | Claude model to use |
| `LLM_MAX_TOKENS` | no | 2048 | Max tokens per response |
| `SMTP_HOST` | for email | smtp.gmail.com | SMTP server hostname |
| `SMTP_PORT` | for email | 587 | SMTP port (587=TLS, 465=SSL) |
| `SMTP_USERNAME` | for email | — | Your email address |
| `SMTP_PASSWORD` | for email | — | App password (not your login password) |
| `SMTP_FROM_EMAIL` | for email | — | Sender address |
| `SMTP_TLS` | no | true | Use STARTTLS |
| `CHROMA_PERSIST_DIR` | no | ./data/chroma | Where ChromaDB stores vectors |
| `CHROMA_COLLECTION` | no | subscription_memory | Base collection name |
| `REMINDER_DAYS_BEFORE` | no | 7 | Send reminder N days before renewal |
| `REMINDER_CHECK_INTERVAL_HOURS` | no | 24 | How often scheduler runs |
| `DEBUG` | no | true | Enables SQL echo + auto-reload |

---

## Running the App

### Development (auto-reload on file changes)
```bash
# Make sure .venv is activated
source .venv/bin/activate   # macOS/Linux
python run.py
```

### Alternative: uvicorn directly
```bash
uvicorn app.main:app --reload --port 8000
```

### Access points
| URL | Description |
|---|---|
| http://localhost:8000 | Frontend (login page) |
| http://localhost:8000/api/docs | Swagger UI — interactive API docs |
| http://localhost:8000/api/redoc | ReDoc API docs |
| http://localhost:8000/api/health | Health check |

---

## Seeding Demo Data

After starting the app at least once (so tables are created):

```bash
python seed.py
```

Output:
```
✅ Tables ready.
✅ Created user: demo@example.com (id=1)
✅ Seeded 15 subscriptions.

🚀 Seed complete!
   Login → Email:    demo@example.com
           Password: Demo1234
```

This creates:
- 1 demo user
- 15 subscriptions across 8 categories
- Several subscriptions with renewal dates in the next 7 days (so you see the "Due This Week" section immediately)

---

## API Reference

All API routes are prefixed with `/api`. Protected routes require `Authorization: Bearer <token>`.

### Authentication

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | ❌ | Register new user |
| POST | `/api/auth/login` | ❌ | Login, get tokens |
| GET  | `/api/auth/me` | ✅ | Current user info |
| POST | `/api/auth/logout` | ✅ | Logout (client-side) |

**Register request body:**
```json
{
  "email": "user@example.com",
  "full_name": "Jane Smith",
  "password": "Secret123"
}
```

**Login / Register response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "email": "...", "full_name": "...", "is_active": true }
}
```

### Subscriptions

| Method | Path | Auth | Description |
|---|---|---|---|
| POST   | `/api/subscriptions`       | ✅ | Create subscription |
| GET    | `/api/subscriptions`       | ✅ | List all (add `?active_only=true`) |
| GET    | `/api/subscriptions/{id}`  | ✅ | Get single |
| PATCH  | `/api/subscriptions/{id}`  | ✅ | Update (partial) |
| DELETE | `/api/subscriptions/{id}`  | ✅ | Delete |

**Create/Update fields:**
```json
{
  "tool_name": "Figma",
  "category": "Design",
  "price": 15.00,
  "currency": "USD",
  "billing_cycle": "monthly",
  "start_date": "2025-01-01",
  "renewal_date": "2025-08-01",
  "website_url": "https://figma.com",
  "notes": "Pro plan"
}
```

Valid `billing_cycle` values: `monthly`, `quarterly`, `yearly`, `lifetime`

Valid `category` values: `Productivity`, `Design`, `Development`, `Communication`, `Storage & Cloud`, `Security`, `Analytics`, `Marketing`, `Finance`, `AI & ML`, `Entertainment`, `Education`, `Other`

### Dashboard

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/dashboard/summary`       | ✅ | Full dashboard metrics |
| GET | `/api/dashboard/renewals`      | ✅ | Upcoming renewals (`?days=30`) |
| GET | `/api/dashboard/insights`      | ✅ | Cost-saving insights |

### AI Chat

| Method | Path | Auth | Description |
|---|---|---|---|
| POST   | `/api/chat`          | ✅ | Send message to assistant |
| GET    | `/api/chat/history`  | ✅ | Get session history (`?session_id=...`) |
| DELETE | `/api/chat/session`  | ✅ | Clear a session (`?session_id=...`) |

**Chat request:**
```json
{
  "message": "What's my total monthly spend?",
  "session_id": null
}
```

**Chat response:**
```json
{
  "session_id": "abc123...",
  "reply": "Your total monthly spend is $156.23 across 12 active subscriptions...",
  "messages": [...]
}
```

### Utilities

| Method | Path | Auth | Description |
|---|---|---|---|
| GET  | `/api/health`                    | ❌ | Health check |
| POST | `/api/admin/reminders/trigger`   | ✅ | Manually trigger reminder check |

---

## Running Tests

### Install test dependencies

```bash
pip install pytest pytest-asyncio httpx
```

### Run all tests

```bash
pytest tests/ -v
```

### Run specific test files

```bash
pytest tests/test_auth.py -v
pytest tests/test_subscriptions.py -v
pytest tests/test_dashboard.py -v
```

### Run with coverage

```bash
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term-missing
```

### Expected output (all passing)

```
tests/test_auth.py::test_register_success         PASSED
tests/test_auth.py::test_register_duplicate_email PASSED
tests/test_auth.py::test_register_weak_password   PASSED
tests/test_auth.py::test_login_success            PASSED
tests/test_auth.py::test_login_wrong_password     PASSED
tests/test_auth.py::test_me_endpoint              PASSED
tests/test_auth.py::test_me_unauthorized          PASSED
tests/test_auth.py::test_health                   PASSED
tests/test_subscriptions.py::test_create_subscription         PASSED
tests/test_subscriptions.py::test_list_subscriptions          PASSED
tests/test_subscriptions.py::test_get_single_subscription     PASSED
tests/test_subscriptions.py::test_update_subscription         PASSED
tests/test_subscriptions.py::test_delete_subscription         PASSED
tests/test_subscriptions.py::test_user_isolation              PASSED
tests/test_subscriptions.py::test_billing_cycle_cost_calculation PASSED
tests/test_subscriptions.py::test_invalid_billing_cycle       PASSED
tests/test_dashboard.py::test_dashboard_empty             PASSED
tests/test_dashboard.py::test_dashboard_monthly_spend      PASSED
tests/test_dashboard.py::test_dashboard_due_this_week      PASSED
tests/test_dashboard.py::test_upcoming_renewals_endpoint   PASSED
tests/test_dashboard.py::test_insights_duplicates          PASSED
tests/test_dashboard.py::test_insights_annual_saving       PASSED
22 passed in X.XXs
```

---

## Manual Testing Checklist

After starting the app, go through this checklist to verify everything works.

### Auth
- [ ] Go to http://localhost:8000 — login page appears
- [ ] Register with a new email/password → redirected to dashboard
- [ ] Logout → back to login page
- [ ] Login with wrong password → error message shown
- [ ] Login with correct credentials → dashboard loads

### Subscriptions
- [ ] Click **Subscriptions** in sidebar → empty state with "Add" button
- [ ] Click **Add Subscription** → modal opens with all fields
- [ ] Fill in tool name, category, price, billing cycle, renewal date → Save
- [ ] Subscription appears in table with correct monthly cost
- [ ] Click **Edit** → modal pre-filled → change price → Save → updated
- [ ] Click **Delete** → confirm dialog → subscription removed
- [ ] Add a yearly subscription ($120/yr) → monthly cost shows $10.00
- [ ] Search box filters by tool name in real time
- [ ] Category filter dropdown works

### Dashboard
- [ ] Add 3+ subscriptions → dashboard shows correct monthly/yearly totals
- [ ] Add a subscription with renewal_date = tomorrow → appears in "Due This Week"
- [ ] Category breakdown cards appear with correct counts
- [ ] Percentages in category bars look correct

### Renewals
- [ ] Click **Renewals** in sidebar → list of upcoming renewals (90-day window)
- [ ] Items with ≤3 days show red left border
- [ ] Items with ≤7 days show orange left border
- [ ] Items with >7 days show green left border

### Insights
- [ ] Click **Insights** → cost-saving suggestions appear
- [ ] Add 2 subs in same category → "Multiple tools in X" insight appears
- [ ] Add monthly sub ($15) → "Switch to annual" insight appears with saving amount

### AI Assistant
- [ ] Click **AI Assistant** → chat panel opens, welcome message shown
- [ ] Type "What is my monthly spend?" → assistant responds with your actual data
- [ ] Click suggestion chip "🔔 This week" → assistant lists due-soon subscriptions
- [ ] Ask "How can I save money?" → assistant calls insights tool and explains
- [ ] Ask "Do I have Figma?" (if you added it) → assistant looks it up
- [ ] Ask about alternatives: "What are alternatives to Slack?" → list appears
- [ ] Start new chat (button top right of chat) → fresh conversation
- [ ] Refresh page → same session resumes from history

### Reminders (requires SMTP configured)
- [ ] POST `/api/admin/reminders/trigger` with your Bearer token
- [ ] Check inbox — email with styled renewal reminder received
- [ ] Trigger again — no duplicate email sent (reminder_log prevents it)

---

## Pushing to GitHub

### First push (new repository)

```bash
# 1. Make sure .env is in .gitignore (it already is)
# 2. Initialize git if you haven't already
git init

# 3. Add all files
git add .

# 4. Verify .env is NOT staged
git status   # .env should not appear

# 5. Commit
git commit -m "Initial commit: Tool Subscription Dashboard"

# 6. Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/tool-subscription-dashboard.git
git branch -M main
git push -u origin main
```

### What gets committed vs ignored

| Committed ✅ | Ignored ❌ |
|---|---|
| All `.py` files | `.env` (your secrets) |
| `static/` frontend | `data/` (SQLite + ChromaDB files) |
| `requirements.txt` | `.venv/` (virtual environment) |
| `.env.example` (no real secrets) | `__pycache__/` |
| `tests/` | `*.db` files |
| `README.md` | `.coverage`, `htmlcov/` |
| `.gitignore` | `logs/` |

### Subsequent pushes

```bash
git add .
git commit -m "describe your changes"
git push
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'app'`
You are running Python from the wrong directory. Always run from the project root:
```bash
cd tool-subscription-dashboard
python run.py
```

### `sqlalchemy.exc.OperationalError: no such table: users`
The `models/__init__.py` file must import all models before `create_tables()` runs:
```python
# app/models/__init__.py  ← this file MUST exist with these imports
from app.models.user import User
from app.models.subscription import Subscription
from app.models.reminder_log import ReminderLog
from app.models.chat_memory import ChatMemory
```

### `401 Unauthorized` on all protected routes
Your JWT token has expired (default: 60 min). Log in again to get a fresh token.

### `ANTHROPIC_API_KEY not set` in chat
Add your API key to `.env`:
```ini
ANTHROPIC_API_KEY=sk-ant-api03-...
```
Restart the server after editing `.env`.

### Email not sending
- Check that 2-Step Verification is ON in your Google account
- Use an **App Password**, not your regular Google password
- App passwords are 16 characters with no spaces
- Test with: `python -c "import asyncio; from app.services.email_service import email_service; asyncio.run(email_service.send_email('your@email.com', 'Test', '<b>Test</b>'))"`

### ChromaDB error on startup
```bash
pip install chromadb --upgrade
```
If the `data/chroma/` directory is corrupted, delete it:
```bash
rm -rf data/chroma/
```

### Port 8000 already in use
```bash
# Find what's using port 8000
lsof -i :8000   # macOS/Linux
netstat -ano | findstr :8000   # Windows

# Or run on a different port
uvicorn app.main:app --port 8001
```

### `SyntaxError` or import errors
Run the syntax check:
```bash
python -c "
import ast, os
for root, dirs, files in os.walk('app'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            try: ast.parse(open(p).read())
            except SyntaxError as e: print('ERROR', p, e)
print('done')
"
```

### Tests fail with `ImportError`
```bash
pip install pytest pytest-asyncio httpx
```
Check that `pytest.ini` or `pyproject.toml` sets asyncio mode. Add a `pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
```

---

## Future Enhancements

These are not in scope for the current project but are clean next steps:

| Enhancement | What to do |
|---|---|
| PostgreSQL | Change `DATABASE_URL` to `postgresql+asyncpg://...`, run `pip install asyncpg` |
| Alembic migrations | `pip install alembic`, `alembic init migrations`, replace `create_tables()` |
| Token refresh | Add `POST /auth/refresh` that accepts a refresh token |
| Password reset | Add forgot-password flow with time-limited reset tokens via email |
| CSV export | Add `GET /api/subscriptions/export` that streams a CSV |
| Recurring date auto-calc | Auto-advance `renewal_date` after a renewal is confirmed |
| Multi-currency | Fetch exchange rates via open.er-api.com to normalise to USD |
| Docker | Add `Dockerfile` + `docker-compose.yml` for one-command deployment |
| Nginx + HTTPS | Reverse proxy for production with Let's Encrypt SSL |
| Rate limiting | `pip install slowapi` — add limits to auth routes |

---

## Project Summary

```
49 Python files    — 100% syntax-checked
3  Frontend files  — HTML + CSS + JS, no build step
22 Tests           — auth, CRUD, dashboard, isolation
4  DB tables       — users, subscriptions, reminder_logs, chat_memories
6  AI tools        — subscriptions, spend, renewals, insights, lookup, alternatives
2  Memory layers   — SQL short-term + ChromaDB long-term
```

---

*Built with FastAPI · SQLAlchemy · Pydantic · Anthropic Claude · ChromaDB*
