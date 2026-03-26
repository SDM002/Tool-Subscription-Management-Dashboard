# 📦 Tool Subscription Management Dashboard
### Powered by LangGraph · Groq · MCP · FastAPI · ChromaDB
This mini project focuses on building a system that helps organizations track and manage the
various software tools and services used internally. Many organizations rely on multiple third-
party tools for engineering, collaboration, and productivity, each with its own billing cycle,
renewal timeline, and cost. Managing these subscriptions manually can become difficult and
may lead to missed renewals or lack of visibility into overall spending.

The goal of this project is to build a centralized system that allows users to record, monitor, and
manage tool subscriptions through a clean dashboard interface. The system should also provide
automated reminders for upcoming subscription renewals and include an intelligent assistant
that allows users to interact with the system through natural language queries.


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



