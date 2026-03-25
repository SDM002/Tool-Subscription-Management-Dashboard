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


