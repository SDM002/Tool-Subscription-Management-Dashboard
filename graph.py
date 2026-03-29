from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel
import os


llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


# ── Subscription tool schemas (shape only — MCP executes) ────

class UserIdInput(BaseModel):
    user_id: int

class RenewalsInput(BaseModel):
    user_id: int
    days: int = 30

class AlternativesInput(BaseModel):
    tool_name: str


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
    description="Get subscriptions renewing within the next N days. Use for 'what renews this week', 'due soon', etc. Use days=7 for this week, days=30 for this month.",
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
    description="Get free or cheaper alternatives to a specific tool like Figma, Notion, Slack, GitHub, Jira, Adobe, Todoist, JetBrains, ChatGPT.",
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

llm_with_tools = llm.bind_tools(tools)


class AgentState(TypedDict):
    messages: List[BaseMessage]


def agent_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}


def tool_node(state: AgentState):
    last_message = state["messages"][-1]
    tool_messages = [
        ToolMessage(
            content="Tool execution delegated to MCP",
            tool_call_id=call["id"]
        )
        for call in last_message.tool_calls
    ]
    return {"messages": state["messages"] + tool_messages}


def should_use_tool(state: AgentState):
    last = state["messages"][-1]
    return "tool" if getattr(last, "tool_calls", None) else END


graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tool", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_use_tool, {"tool": "tool", END: END})
graph.add_edge("tool", "agent")
agent_graph = graph.compile()
