"""
app/tools/recommendation_tool.py  [NEW]

Tool function: get_spending_insights
Wraps the pricing service for the assistant to call.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.pricing_service import pricing_service


async def get_spending_insights(db: AsyncSession, user_id: int) -> dict:
    """
    Return rule-based cost-saving insights:
    - duplicate tools per category
    - potential savings from annual billing
    - high-cost subscription alerts
    """
    insights = await pricing_service.get_insights(db, user_id)
    return {
        "count": len(insights),
        "insights": [
            {
                "type": i.type,
                "title": i.title,
                "detail": i.detail,
                "affected_tools": i.affected_tools,
                "potential_saving": i.potential_saving,
            }
            for i in insights
        ],
    }


# Static knowledge base of popular alternatives
ALTERNATIVE_TOOLS: dict[str, list[dict]] = {
    "figma": [
        {"name": "Penpot", "price": "Free (self-hosted)", "url": "https://penpot.app"},
        {"name": "Lunacy", "price": "Free", "url": "https://icons8.com/lunacy"},
    ],
    "notion": [
        {"name": "Obsidian", "price": "Free (local)", "url": "https://obsidian.md"},
        {"name": "AppFlowy", "price": "Free (open source)", "url": "https://appflowy.io"},
        {"name": "Logseq", "price": "Free", "url": "https://logseq.com"},
    ],
    "slack": [
        {"name": "Discord", "price": "Free", "url": "https://discord.com"},
        {"name": "Mattermost", "price": "Free (self-hosted)", "url": "https://mattermost.com"},
        {"name": "Zulip", "price": "Free (open source)", "url": "https://zulip.com"},
    ],
    "github": [
        {"name": "GitLab", "price": "Free tier available", "url": "https://gitlab.com"},
        {"name": "Gitea", "price": "Free (self-hosted)", "url": "https://gitea.io"},
    ],
    "jira": [
        {"name": "Linear", "price": "Free tier", "url": "https://linear.app"},
        {"name": "Plane", "price": "Free (open source)", "url": "https://plane.so"},
        {"name": "YouTrack", "price": "Free up to 10 users", "url": "https://jetbrains.com/youtrack"},
    ],
    "zoom": [
        {"name": "Google Meet", "price": "Free with Google account", "url": "https://meet.google.com"},
        {"name": "Jitsi", "price": "Free (self-hosted)", "url": "https://jitsi.org"},
    ],
    "dropbox": [
        {"name": "Nextcloud", "price": "Free (self-hosted)", "url": "https://nextcloud.com"},
        {"name": "Mega", "price": "20GB free", "url": "https://mega.io"},
    ],
    "grammarly": [
        {"name": "LanguageTool", "price": "Free tier", "url": "https://languagetool.org"},
        {"name": "Hemingway App", "price": "One-time $19.99", "url": "https://hemingwayapp.com"},
    ],
}


def get_alternatives(tool_name: str) -> dict:
    """Return known free/cheaper alternatives for a tool."""
    name_lower = tool_name.lower()
    for key, alts in ALTERNATIVE_TOOLS.items():
        if key in name_lower or name_lower in key:
            return {
                "tool": tool_name,
                "alternatives": alts,
                "found": True,
            }
    return {
        "tool": tool_name,
        "alternatives": [],
        "found": False,
        "message": f"No specific alternatives found for '{tool_name}' in the knowledge base.",
    }
