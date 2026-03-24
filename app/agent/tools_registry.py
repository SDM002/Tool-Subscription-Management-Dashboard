"""
app/agent/tools_registry.py  [NEW]

Defines tools for the Anthropic Claude function-calling API.
Each entry in TOOL_DEFINITIONS maps to a Python function in TOOL_HANDLERS.

The assistant_service calls `dispatch_tool()` when the LLM requests a tool.
"""

import json
from sqlalchemy.ext.asyncio import AsyncSession

# ── Tool schemas for Anthropic API ───────────────────────────
TOOL_DEFINITIONS = [
    {
        "name": "get_subscriptions",
        "description": (
            "Fetch all active subscriptions for the user. "
            "Returns tool name, category, price, billing cycle, renewal date, and costs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_spending_summary",
        "description": (
            "Get the user's total monthly and yearly subscription spend, "
            "broken down by category."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_upcoming_renewals",
        "description": (
            "Get subscriptions renewing within the next N days. "
            "Use this to answer questions like 'what renews this week' or 'what's due soon'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Look-ahead window in days (default 30, max 365)",
                    "default": 30,
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_spending_insights",
        "description": (
            "Get cost-saving suggestions: duplicate tools in same category, "
            "potential savings from switching to annual billing, high-cost alerts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_subscription_by_name",
        "description": (
            "Look up a specific subscription by tool name. "
            "Useful when the user asks about a specific tool."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name (or partial name) of the tool to look up",
                }
            },
            "required": ["name"],
        },
    },
    {
        "name": "get_alternatives",
        "description": (
            "Get free or cheaper alternatives to a specific tool. "
            "Useful for cost-saving suggestions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "The name of the tool to find alternatives for",
                }
            },
            "required": ["tool_name"],
        },
    },
]


async def dispatch_tool(
    tool_name: str,
    tool_input: dict,
    db: AsyncSession,
    user_id: int,
) -> str:
    """
    Execute the named tool and return the result as a JSON string.
    This is called by assistant_service when the LLM requests a tool.
    """
    from app.tools.spend_analysis import (
        get_subscriptions,
        get_spending_summary,
        get_subscription_by_name,
    )
    from app.tools.renewal_analysis import get_upcoming_renewals
    from app.tools.recommendation_tool import get_spending_insights

    try:
        if tool_name == "get_subscriptions":
            result = await get_subscriptions(db, user_id)

        elif tool_name == "get_spending_summary":
            result = await get_spending_summary(db, user_id)

        elif tool_name == "get_upcoming_renewals":
            days = tool_input.get("days", 30)
            result = await get_upcoming_renewals(db, user_id, days=days)

        elif tool_name == "get_spending_insights":
            result = await get_spending_insights(db, user_id)

        elif tool_name == "get_subscription_by_name":
            name = tool_input.get("name", "")
            result = await get_subscription_by_name(db, user_id, name)

        elif tool_name == "get_alternatives":
            tool_name_input = tool_input.get("tool_name", "")
            from app.tools.alternative_lookup import lookup_alternatives
            result = lookup_alternatives(tool_name_input)

        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return json.dumps(result, default=str)

    except Exception as exc:
        return json.dumps({"error": str(exc)})
