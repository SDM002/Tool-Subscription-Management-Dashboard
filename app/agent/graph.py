import os
from typing import TypedDict, List

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from app.core.config import settings


# ── LLM (Groq) ───────────────────────────────────────────────
# Set the API key in the environment for langchain_groq to pick up
os.environ["GROQ_API_KEY"] = settings.groq_api_key

llm = ChatGroq(
    model=settings.groq_model,
    temperature=0,
)


# ── Tool input schemas (shape only — no execution) ────────────

class UserIdInput(BaseModel):
    user_id: int

class RenewalsInput(BaseModel):
    user_id: int
    days: int = 30

class AlternativesInput(BaseModel):
    tool_name: str


# ── Tool definitions (schema only — MCP executes them) ────────

get_subscriptions_tool = StructuredTool(
    name="get_subscriptions",
    description="Fetch all active subscriptions for the user. Returns tool name, category, price, billing cycle, renewal date, monthly and yearly cost.",
    args_schema=UserIdInput,
    func=lambda **kwargs: None,
)

get_spending_summary_tool = StructuredTool(
    name="get_spending_summary",
    description="Get total monthly and yearly subscription spend broken down by category.",
    args_schema=UserIdInput,
    func=lambda **kwargs: None,
)

get_upcoming_renewals_tool = StructuredTool(
    name="get_upcoming_renewals",
    description="Get subscriptions renewing within the next N days. Use for 'what renews this week', 'due soon', etc.",
    args_schema=RenewalsInput,
    func=lambda **kwargs: None,
)

get_spending_insights_tool = StructuredTool(
    name="get_spending_insights",
    description="Get cost-saving suggestions: duplicate tools in same category, annual billing savings, high-cost alerts.",
    args_schema=UserIdInput,
    func=lambda **kwargs: None,
)

get_alternatives_tool = StructuredTool(
    name="get_alternatives",
    description="Get free or cheaper alternatives to a specific tool like Figma, Notion, Slack, GitHub, Jira.",
    args_schema=AlternativesInput,
    func=lambda **kwargs: None,
)

tools = [
    get_subscriptions_tool,
    get_spending_summary_tool,
    get_upcoming_renewals_tool,
    get_spending_insights_tool,
    get_alternatives_tool,
]

# Bind tool schemas to LLM so it knows what tools are available
llm_with_tools = llm.bind_tools(tools)


# ── State ─────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: List[BaseMessage]


# ── Agent node — LLM decides: answer directly OR call a tool ──

def agent_node(state: AgentState) -> dict:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}


# ── Tool node — PLACEHOLDER only ──────────────────────────────
# Real execution is done in agent_runner.py via MCPClient.
# This node exists only to satisfy LangGraph's edge requirements.
# agent_runner intercepts before this runs and injects real results.

def tool_node(state: AgentState) -> dict:
    last = state["messages"][-1]
    tool_messages = [
        ToolMessage(
            content="Tool execution delegated to MCP",
            tool_call_id=call["id"],
        )
        for call in last.tool_calls
    ]
    return {"messages": state["messages"] + tool_messages}


# ── Router — directs to tool or END ───────────────────────────

def should_use_tool(state: AgentState) -> str:
    last = state["messages"][-1]
    return "tool" if getattr(last, "tool_calls", None) else END


# ── Build the graph ───────────────────────────────────────────

graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tool",  tool_node)

graph.set_entry_point("agent")

graph.add_conditional_edges(
    "agent",
    should_use_tool,
    {"tool": "tool", END: END},
)

# After tool execution → back to agent (the loop)
graph.add_edge("tool", "agent")

agent_graph = graph.compile()
