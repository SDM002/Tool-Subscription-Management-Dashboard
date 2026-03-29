import json
import sys
import os
import sqlite3
from datetime import date, timedelta
from collections import defaultdict

# DB path — resolves relative to this file's location
DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data", "subscriptions.db"
)

ALTERNATIVES_DB = {
    "figma":      [{"name": "Penpot",       "price": "Free (open source)", "url": "https://penpot.app"},
                   {"name": "Lunacy",       "price": "Free",               "url": "https://icons8.com/lunacy"}],
    "notion":     [{"name": "Obsidian",     "price": "Free (local)",       "url": "https://obsidian.md"},
                   {"name": "AppFlowy",     "price": "Free (open source)", "url": "https://appflowy.io"},
                   {"name": "Logseq",       "price": "Free",               "url": "https://logseq.com"}],
    "slack":      [{"name": "Discord",      "price": "Free",               "url": "https://discord.com"},
                   {"name": "Mattermost",   "price": "Free (self-hosted)", "url": "https://mattermost.com"},
                   {"name": "Zulip",        "price": "Free (open source)", "url": "https://zulip.com"}],
    "github":     [{"name": "GitLab",       "price": "Free tier",          "url": "https://gitlab.com"},
                   {"name": "Gitea",        "price": "Free (self-hosted)", "url": "https://gitea.io"}],
    "dropbox":    [{"name": "Nextcloud",    "price": "Free (self-hosted)", "url": "https://nextcloud.com"},
                   {"name": "Mega",         "price": "20 GB free",         "url": "https://mega.io"}],
    "1password":  [{"name": "Bitwarden",    "price": "Free (open source)", "url": "https://bitwarden.com"},
                   {"name": "KeePassXC",    "price": "Free (local)",       "url": "https://keepassxc.org"}],
    "loom":       [{"name": "OBS Studio",   "price": "Free (open source)", "url": "https://obsproject.com"},
                   {"name": "Cap",          "price": "Free tier",          "url": "https://cap.so"}],
    "vercel":     [{"name": "Netlify",      "price": "Free tier",          "url": "https://netlify.com"},
                   {"name": "Cloudflare Pages", "price": "Free tier",      "url": "https://pages.cloudflare.com"}],
    "todoist":    [{"name": "TickTick",     "price": "Free tier",          "url": "https://ticktick.com"},
                   {"name": "Things 3",     "price": "$49.99 one-time",    "url": "https://culturedcode.com"}],
    "chatgpt":    [{"name": "Claude",       "price": "Free tier",          "url": "https://claude.ai"},
                   {"name": "Gemini",       "price": "Free tier",          "url": "https://gemini.google.com"},
                   {"name": "Mistral",      "price": "Free tier",          "url": "https://mistral.ai"}],
    "jetbrains":  [{"name": "VS Code",      "price": "Free",               "url": "https://code.visualstudio.com"},
                   {"name": "Neovim",       "price": "Free",               "url": "https://neovim.io"},
                   {"name": "Zed",          "price": "Free",               "url": "https://zed.dev"}],
    "adobe":      [{"name": "Canva",        "price": "Free tier",          "url": "https://canva.com"},
                   {"name": "GIMP",         "price": "Free",               "url": "https://gimp.org"},
                   {"name": "Inkscape",     "price": "Free",               "url": "https://inkscape.org"}],
    "mixpanel":   [{"name": "PostHog",      "price": "Free tier",          "url": "https://posthog.com"},
                   {"name": "Plausible",    "price": "Free self-hosted",   "url": "https://plausible.io"}],
    "genspark":   [{"name": "Perplexity",   "price": "Free tier",          "url": "https://perplexity.ai"},
                   {"name": "You.com",      "price": "Free",               "url": "https://you.com"}],
    "aws":        [{"name": "Google Cloud", "price": "Free tier",          "url": "https://cloud.google.com"},
                   {"name": "Hetzner",      "price": "From €3.29/mo",      "url": "https://hetzner.com"}],
}


def _conn():
    return sqlite3.connect(DB_PATH)


def tool_get_subscriptions(user_id: int) -> dict:
    with _conn() as db:
        rows = db.execute(
            "SELECT id, tool_name, category, price, currency, billing_cycle, "
            "renewal_date, start_date, notes "
            "FROM subscriptions WHERE user_id=? AND is_active=1 ORDER BY renewal_date",
            (user_id,)
        ).fetchall()

    subs = []
    for r in rows:
        price   = r[3] or 0.0
        cycle   = (r[5] or "monthly").lower()
        monthly = price if cycle == "monthly" else \
                  round(price / 3, 2) if cycle == "quarterly" else \
                  round(price / 12, 2) if cycle == "yearly" else price
        yearly  = round(price * 12, 2) if cycle == "monthly" else \
                  round(price * 4,  2) if cycle == "quarterly" else \
                  price if cycle == "yearly" else price
        subs.append({
            "id": r[0], "tool_name": r[1], "category": r[2],
            "price": price, "currency": r[4] or "USD",
            "billing_cycle": cycle, "renewal_date": r[6],
            "start_date": r[7], "notes": r[8],
            "monthly_cost": monthly, "yearly_cost": yearly,
        })
    return {"count": len(subs), "subscriptions": subs}


def tool_get_spending_summary(user_id: int) -> dict:
    data = tool_get_subscriptions(user_id)
    subs = data["subscriptions"]
    total_monthly = round(sum(s["monthly_cost"] for s in subs), 2)
    total_yearly  = round(sum(s["yearly_cost"]  for s in subs), 2)
    by_cat = defaultdict(lambda: {"monthly": 0.0, "yearly": 0.0, "tools": []})
    for s in subs:
        by_cat[s["category"]]["monthly"] += s["monthly_cost"]
        by_cat[s["category"]]["yearly"]  += s["yearly_cost"]
        by_cat[s["category"]]["tools"].append(s["tool_name"])
    return {
        "active_count": len(subs),
        "total_monthly": total_monthly,
        "total_yearly": total_yearly,
        "by_category": [
            {"category": c, "monthly": round(v["monthly"], 2),
             "yearly": round(v["yearly"], 2), "tools": v["tools"]}
            for c, v in sorted(by_cat.items(), key=lambda x: x[1]["monthly"], reverse=True)
        ],
    }


def tool_get_upcoming_renewals(user_id: int, days: int = 30) -> dict:
    today    = date.today()
    end_date = today + timedelta(days=days)
    with _conn() as db:
        rows = db.execute(
            "SELECT id, tool_name, category, price, currency, billing_cycle, renewal_date "
            "FROM subscriptions WHERE user_id=? AND is_active=1 "
            "AND renewal_date>=? AND renewal_date<=? ORDER BY renewal_date",
            (user_id, today.isoformat(), end_date.isoformat())
        ).fetchall()
    return {
        "window_days": days, "count": len(rows),
        "renewals": [
            {"id": r[0], "tool_name": r[1], "category": r[2],
             "price": r[3], "currency": r[4], "billing_cycle": r[5],
             "renewal_date": r[6],
             "days_until_renewal": (date.fromisoformat(r[6]) - today).days}
            for r in rows
        ],
    }


def tool_get_spending_insights(user_id: int) -> dict:
    data = tool_get_subscriptions(user_id)
    subs = data["subscriptions"]
    insights = []
    cat_tools = defaultdict(list)
    for s in subs:
        cat_tools[s["category"]].append(s["tool_name"])
    for cat, tools in cat_tools.items():
        if len(tools) >= 2:
            insights.append({"type": "duplicate",
                "title": f"Multiple tools in '{cat}'",
                "detail": f"You have {len(tools)} tools in '{cat}': {', '.join(tools)}. Consider consolidating.",
                "affected_tools": tools, "potential_saving": 0.0})
    for s in subs:
        if s["billing_cycle"] == "monthly" and s["price"] > 5:
            annual = s["price"] * 12
            saving = round(annual * 0.17, 2)
            insights.append({"type": "annual_saving",
                "title": f"Switch '{s['tool_name']}' to annual billing",
                "detail": f"Monthly costs ${annual:.2f}/yr. Annual plans save ~17% (≈${saving:.2f}/yr).",
                "affected_tools": [s["tool_name"]], "potential_saving": saving})
    for s in subs:
        if s["monthly_cost"] > 50:
            insights.append({"type": "high_cost",
                "title": f"High spend on '{s['tool_name']}'",
                "detail": f"Costs ${s['monthly_cost']:.2f}/mo. Review usage.",
                "affected_tools": [s["tool_name"]], "potential_saving": 0.0})
    total_m = round(sum(s["monthly_cost"] for s in subs), 2)
    total_y = round(sum(s["yearly_cost"]  for s in subs), 2)
    insights.append({"type": "summary",
        "title": "Total subscription spend",
        "detail": f"{len(subs)} active subscriptions costing ${total_m:.2f}/month (${total_y:.2f}/year).",
        "affected_tools": [], "potential_saving": 0.0})
    insights.sort(key=lambda x: x["potential_saving"], reverse=True)
    return {"count": len(insights), "insights": insights}


def tool_get_alternatives(tool_name: str) -> dict:
    name_lower = tool_name.lower().strip()
    for key, alts in ALTERNATIVES_DB.items():
        if key in name_lower or name_lower in key:
            return {"tool": tool_name, "found": True, "alternatives": alts}
    return {"tool": tool_name, "found": False, "alternatives": [],
            "message": f"No specific alternatives for '{tool_name}'. Try https://alternativeto.net"}


TOOLS = {
    "get_subscriptions":     lambda args: tool_get_subscriptions(int(args.get("user_id", 0))),
    "get_spending_summary":  lambda args: tool_get_spending_summary(int(args.get("user_id", 0))),
    "get_upcoming_renewals": lambda args: tool_get_upcoming_renewals(int(args.get("user_id", 0)), int(args.get("days", 30))),
    "get_spending_insights": lambda args: tool_get_spending_insights(int(args.get("user_id", 0))),
    "get_alternatives":      lambda args: tool_get_alternatives(args.get("tool_name") or args.get("name") or "unknown"),
}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request   = json.loads(line)
            method    = request.get("method", "")
            req_id    = request.get("id")
            if method == "tools/call":
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
    main()
