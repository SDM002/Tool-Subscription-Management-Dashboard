import json
import sys
import os
import sqlite3
from datetime import date, timedelta
from collections import defaultdict

# Use the directory where the server is actually launched from (project root)
# Fall back to __file__-relative path if CWD doesn't have the DB
_cwd_path  = os.path.join(os.getcwd(), "data", "subscriptions.db")
_file_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "subscriptions.db"
)
DB_PATH = _cwd_path if os.path.exists(_cwd_path) else _file_path

# ── Alternatives knowledge base ───────────────────────────────
ALTERNATIVES_DB: dict[str, list[dict]] = {
    "figma":      [{"name": "Penpot",       "price": "Free (open source)", "url": "https://penpot.app"},
                   {"name": "Lunacy",        "price": "Free",               "url": "https://icons8.com/lunacy"}],
    "notion":     [{"name": "Obsidian",      "price": "Free (local)",       "url": "https://obsidian.md"},
                   {"name": "AppFlowy",      "price": "Free (open source)", "url": "https://appflowy.io"},
                   {"name": "Logseq",        "price": "Free",               "url": "https://logseq.com"}],
    "slack":      [{"name": "Discord",       "price": "Free",               "url": "https://discord.com"},
                   {"name": "Mattermost",    "price": "Free (self-hosted)", "url": "https://mattermost.com"},
                   {"name": "Zulip",         "price": "Free (open source)", "url": "https://zulip.com"}],
    "github":     [{"name": "GitLab",        "price": "Free tier",          "url": "https://gitlab.com"},
                   {"name": "Gitea",         "price": "Free (self-hosted)", "url": "https://gitea.io"}],
    "jira":       [{"name": "Linear",        "price": "Free tier",          "url": "https://linear.app"},
                   {"name": "Plane",         "price": "Free (open source)", "url": "https://plane.so"}],
    "zoom":       [{"name": "Google Meet",   "price": "Free with Google",   "url": "https://meet.google.com"},
                   {"name": "Jitsi Meet",    "price": "Free (open source)", "url": "https://meet.jit.si"}],
    "dropbox":    [{"name": "Nextcloud",     "price": "Free (self-hosted)", "url": "https://nextcloud.com"},
                   {"name": "Mega",          "price": "20 GB free",         "url": "https://mega.io"}],
    "grammarly":  [{"name": "LanguageTool",  "price": "Free tier",          "url": "https://languagetool.org"},
                   {"name": "Hemingway",     "price": "$19.99 one-time",    "url": "https://hemingwayapp.com"}],
    "trello":     [{"name": "Planka",        "price": "Free (self-hosted)", "url": "https://planka.app"},
                   {"name": "Wekan",         "price": "Free (self-hosted)", "url": "https://wekan.github.io"}],
    "1password":  [{"name": "Bitwarden",     "price": "Free (open source)", "url": "https://bitwarden.com"},
                   {"name": "KeePassXC",     "price": "Free (local)",       "url": "https://keepassxc.org"}],
    "loom":       [{"name": "OBS Studio",    "price": "Free (open source)", "url": "https://obsproject.com"},
                   {"name": "Cap",           "price": "Free tier",          "url": "https://cap.so"}],
    "vercel":     [{"name": "Netlify",       "price": "Free tier",          "url": "https://netlify.com"},
                   {"name": "Cloudflare Pages", "price": "Free tier",       "url": "https://pages.cloudflare.com"}],
    "adobe":      [{"name": "GIMP",          "price": "Free (open source)", "url": "https://gimp.org"},
                   {"name": "Canva",         "price": "Free tier",          "url": "https://canva.com"}],
    "chatgpt":    [{"name": "Groq (llama)",  "price": "Free API",           "url": "https://console.groq.com"},
                   {"name": "Claude",        "price": "Free tier",          "url": "https://claude.ai"}],
    "todoist":    [{"name": "TickTick",   "price": "Free tier", "url": "https://ticktick.com"},
                   {"name": "Things 3",   "price": "$49.99 one-time", "url": "https://culturedcode.com"}],
    "jetbrains":  [{"name": "VS Code",    "price": "Free",      "url": "https://code.visualstudio.com"},
                   {"name": "Neovim",     "price": "Free",      "url": "https://neovim.io"}],
    "mixpanel":   [{"name": "PostHog",       "price": "Free (open source)", "url": "https://posthog.com"},
                   {"name": "Plausible",     "price": "$9/mo",              "url": "https://plausible.io"}],
}


# ── Helper: get a DB connection ───────────────────────────────
def _conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


# ── Tool: get_subscriptions ───────────────────────────────────
def tool_get_subscriptions(user_id: int) -> dict:
    """Return all active subscriptions for this user."""
    with _conn() as db:
        rows = db.execute(
            "SELECT id, tool_name, category, price, currency, billing_cycle, "
            "       renewal_date, start_date, notes "
            "FROM subscriptions "
            "WHERE user_id=? AND is_active=1 "
            "ORDER BY tool_name",
            (user_id,)
        ).fetchall()

    subs = []
    for r in rows:
        price   = r[3] or 0.0
        cycle   = r[5] or "monthly"
        monthly = price if cycle == "monthly" else \
                  round(price / 3, 2) if cycle == "quarterly" else \
                  round(price / 12, 2) if cycle == "yearly" else 0.0
        yearly  = round(price * 12, 2) if cycle == "monthly" else \
                  round(price * 4, 2)  if cycle == "quarterly" else \
                  price if cycle == "yearly" else price

        subs.append({
            "id": r[0], "tool_name": r[1], "category": r[2],
            "price": price, "currency": r[4], "billing_cycle": cycle,
            "renewal_date": r[6], "start_date": r[7], "notes": r[8],
            "monthly_cost": monthly, "yearly_cost": yearly,
        })

    return {"count": len(subs), "subscriptions": subs}


# ── Tool: get_spending_summary ────────────────────────────────
def tool_get_spending_summary(user_id: int) -> dict:
    """Monthly/yearly totals + breakdown by category."""
    data = tool_get_subscriptions(user_id)
    subs = data["subscriptions"]

    total_monthly = round(sum(s["monthly_cost"] for s in subs), 2)
    total_yearly  = round(sum(s["yearly_cost"]  for s in subs), 2)

    by_cat: dict[str, dict] = defaultdict(lambda: {"monthly": 0.0, "yearly": 0.0, "tools": []})
    for s in subs:
        by_cat[s["category"]]["monthly"] += s["monthly_cost"]
        by_cat[s["category"]]["yearly"]  += s["yearly_cost"]
        by_cat[s["category"]]["tools"].append(s["tool_name"])

    return {
        "active_count":  len(subs),
        "total_monthly": total_monthly,
        "total_yearly":  total_yearly,
        "by_category": [
            {
                "category": cat,
                "monthly":  round(v["monthly"], 2),
                "yearly":   round(v["yearly"],  2),
                "tools":    v["tools"],
            }
            for cat, v in sorted(by_cat.items(), key=lambda x: x[1]["monthly"], reverse=True)
        ],
    }


# ── Tool: get_upcoming_renewals ───────────────────────────────
def tool_get_upcoming_renewals(user_id: int, days: int = 30) -> dict:
    """Subscriptions renewing within the next N days."""
    today    = date.today()
    end_date = today + timedelta(days=days)

    with _conn() as db:
        rows = db.execute(
            "SELECT id, tool_name, category, price, currency, billing_cycle, renewal_date "
            "FROM subscriptions "
            "WHERE user_id=? AND is_active=1 AND renewal_date IS NOT NULL "
            "  AND renewal_date >= ? AND renewal_date <= ? "
            "ORDER BY renewal_date",
            (user_id, today.isoformat(), end_date.isoformat())
        ).fetchall()

    renewals = []
    for r in rows:
        rd        = r[6]
        days_left = (date.fromisoformat(rd) - today).days if rd else None
        renewals.append({
            "id": r[0], "tool_name": r[1], "category": r[2],
            "price": r[3], "currency": r[4], "billing_cycle": r[5],
            "renewal_date": rd, "days_until_renewal": days_left,
        })

    return {"count": len(renewals), "days_window": days, "renewals": renewals}


# ── Tool: get_spending_insights ───────────────────────────────
def tool_get_spending_insights(user_id: int) -> dict:
    """Cost-saving suggestions: duplicates, annual savings, high-cost alerts."""
    data     = tool_get_subscriptions(user_id)
    subs     = data["subscriptions"]
    insights = []

    # Duplicate tools in same category
    cat_tools: dict[str, list] = defaultdict(list)
    for s in subs:
        cat_tools[s["category"]].append(s)

    for cat, tools in cat_tools.items():
        if len(tools) >= 2:
            names = [t["tool_name"] for t in tools]
            total = round(sum(t["monthly_cost"] for t in tools), 2)
            insights.append({
                "type":           "duplicate",
                "title":          f"Multiple tools in '{cat}'",
                "detail":         f"You have {len(tools)} tools in '{cat}': {', '.join(names)}. Consider consolidating.",
                "affected_tools": names,
                "potential_saving": round(min(t["monthly_cost"] for t in tools) * 12, 2),
            })

    # Annual billing savings (~17%)
    for s in subs:
        if s["billing_cycle"] == "monthly" and s["monthly_cost"] >= 10:
            annual_current = s["yearly_cost"]
            annual_saving  = round(annual_current * 0.17, 2)
            insights.append({
                "type":           "annual_saving",
                "title":          f"Switch '{s['tool_name']}' to annual billing",
                "detail":         f"Monthly costs ${annual_current:.2f}/yr. Annual plans typically save ~17%.",
                "affected_tools": [s["tool_name"]],
                "potential_saving": annual_saving,
            })

    # High-cost alerts
    for s in subs:
        if s["monthly_cost"] >= 40:
            insights.append({
                "type":           "high_cost",
                "title":          f"High spend on '{s['tool_name']}'",
                "detail":         f"Costs ${s['monthly_cost']:.2f}/mo (${s['yearly_cost']:.2f}/yr). Review usage.",
                "affected_tools": [s["tool_name"]],
                "potential_saving": 0,
            })

    # Summary insight
    total_monthly = round(sum(s["monthly_cost"] for s in subs), 2)
    insights.append({
        "type":           "summary",
        "title":          "Total subscription spend",
        "detail":         f"{len(subs)} active subscriptions costing ${total_monthly:.2f}/month.",
        "affected_tools": [],
        "potential_saving": 0,
    })

    return {"count": len(insights), "insights": insights}


# ── Tool: get_alternatives ────────────────────────────────────
def tool_get_alternatives(tool_name: str) -> dict:
    """Get free or cheaper alternatives for a specific tool."""
    name_lower = tool_name.lower().strip()
    # Try exact match first, then partial match
    for key, alts in ALTERNATIVES_DB.items():
        if key in name_lower or name_lower in key:
            return {"tool": tool_name, "found": True, "alternatives": alts}
    return {
        "tool": tool_name, "found": False, "alternatives": [],
        "message": f"No specific alternatives for '{tool_name}' in the knowledge base. "
                   "Consider searching AlternativeTo.net for community suggestions.",
    }


# ── Tool dispatcher ───────────────────────────────────────────
TOOLS = {
    "get_subscriptions":     lambda args: tool_get_subscriptions(
        int(args.get("user_id", args.get("userId", 0)))
    ),
    "get_spending_summary":  lambda args: tool_get_spending_summary(
        int(args.get("user_id", args.get("userId", 0)))
    ),
    "get_upcoming_renewals": lambda args: tool_get_upcoming_renewals(
        int(args.get("user_id", args.get("userId", 0))),
        int(args.get("days", 30))
    ),
    "get_spending_insights": lambda args: tool_get_spending_insights(
        int(args.get("user_id", args.get("userId", 0)))
    ),
    "get_alternatives":      lambda args: tool_get_alternatives(
        args.get("tool_name") or args.get("name") or args.get("toolName") or "unknown"
    ),
}

TOOL_SCHEMAS = [
    {
        "name": "get_subscriptions",
        "description": "Fetch all active subscriptions for the user. Returns tool name, category, price, billing cycle, renewal date, monthly and yearly cost.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "The user ID to fetch subscriptions for"}
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_spending_summary",
        "description": "Get total monthly and yearly subscription spend broken down by category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "The user ID"}
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_upcoming_renewals",
        "description": "Get subscriptions renewing within the next N days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "The user ID"},
                "days":    {"type": "integer", "description": "Number of days to look ahead (default 30)"},
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_spending_insights",
        "description": "Get cost-saving suggestions: duplicate tools, annual billing savings, high-cost alerts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "The user ID"}
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_alternatives",
        "description": "Get free or cheaper alternatives to a specific tool like Figma, Notion, Slack, GitHub, Jira.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "Name of the tool to find alternatives for"}
            },
            "required": ["tool_name"],
        },
    },
]


# ── JSON-RPC server loop ──────────────────────────────────────
def serve():
    """
    Reads JSON-RPC requests from stdin, writes responses to stdout.
    Runs forever until stdin is closed.
    """
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        response = {}
        try:
            request  = json.loads(line)
            req_id   = request.get("id")
            method   = request.get("method", "")

            if method == "tools/list":
                response = {"id": req_id, "result": TOOL_SCHEMAS}

            elif method == "tools/call":
                params    = request.get("params", {})
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})

                if tool_name not in TOOLS:
                    response = {"id": req_id, "error": f"Unknown tool: {tool_name}"}
                else:
                    try:
                        result   = TOOLS[tool_name](arguments)
                        response = {"id": req_id, "result": json.dumps(result)}
                    except Exception as exc:
                        response = {"id": req_id, "error": str(exc)}
            else:
                response = {"id": req_id, "error": f"Unknown method: {method}"}

        except Exception as exc:
            response = {"id": None, "error": str(exc)}

        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    serve()