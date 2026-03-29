import sys
import json
import traceback
from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from app.agent.graph import agent_graph
from app.mcp.client import MCPClient

CHUNK_SIZE = 20


def is_greeting(text: str) -> bool:
    return text.lower().strip() in {"hi", "hello", "hey", "good morning", "good evening", "good afternoon"}


def is_weak_response(text: str) -> bool:
    if len(text.strip()) < 15:
        return True
    weak = ["i'm not sure", "i am not sure", "i don't know", "i do not know",
            "as an ai", "cannot answer", "not sure", "i cannot"]
    return any(p in text.lower() for p in weak)


def build_system_prompt(user_id: int) -> str:
    return f"""You are an intelligent subscription management assistant.

You have access to these tools — ALWAYS call them to get real data before answering:
  - get_subscriptions:      List all active subscriptions with prices and renewal dates
  - get_spending_summary:   Total monthly/yearly spend broken down by category
  - get_upcoming_renewals:  Renewals due in the next N days
  - get_spending_insights:  Duplicate tools, billing savings, high-cost alerts
  - get_alternatives:       Free or cheaper alternatives to a specific tool

CRITICAL RULES:
- ALWAYS call a tool before answering any subscription question — never guess
- For "show subscriptions / what do I have" → call get_subscriptions
- For "total spend / monthly cost" → call get_spending_summary
- For "renews this week" → call get_upcoming_renewals with user_id={user_id} and days=7
- For "renews this month" → call get_upcoming_renewals with user_id={user_id} and days=30
- For "duplicates / savings / insights" → call get_spending_insights
- For "alternatives to X" → call get_alternatives with the tool name
- The user_id for ALL tools is: {user_id}
- Today's date is: {date.today().isoformat()}
- "spent last month / this week" = no billing history stored; give current monthly cost instead
- If tool returns count=0 subscriptions, say exactly that — do not invent data
"""


def main():
    mcp_client = MCPClient()

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                continue

            data       = json.loads(line)
            user_input = data.get("message", "").strip()
            user_id    = int(data.get("user_id", 0))

            messages = [
                SystemMessage(content=build_system_prompt(user_id)),
                HumanMessage(content=user_input),
            ]

            # Agentic tool loop — max 6 iterations
            for _ in range(6):
                result   = agent_graph.invoke({"messages": messages})
                messages = result["messages"]
                last     = messages[-1]

                # No tool calls → LLM gave a final answer
                if not getattr(last, "tool_calls", None):
                    break

                # Execute each tool call via MCP
                tool_messages = []
                for call in last.tool_calls:
                    tool_name = call["name"]
                    tool_args = dict(call["args"])
                    # Always ensure user_id is set
                    if "user_id" not in tool_args:
                        tool_args["user_id"] = user_id

                    try:
                        result_data = mcp_client.call_tool(tool_name, tool_args)
                        # result_data is already a JSON string from server.py
                        # do NOT double-encode with json.dumps()
                        content = result_data if isinstance(result_data, str) else json.dumps(result_data)
                    except Exception as exc:
                        content = json.dumps({"error": str(exc)})

                    tool_messages.append(
                        ToolMessage(content=content, tool_call_id=call["id"])
                    )

                messages = messages + tool_messages

            response_text = messages[-1].content or "I could not generate a response."

            # Guardrail retry on weak responses
            if not is_greeting(user_input) and is_weak_response(response_text):
                messages.insert(1, SystemMessage(content=(
                    "Answer confidently using the tool data you retrieved. "
                    "Give specific numbers and dates. Do not say you are unsure."
                )))
                result        = agent_graph.invoke({"messages": messages})
                response_text = result["messages"][-1].content or response_text

            # Stream response
            for i in range(0, len(response_text), CHUNK_SIZE):
                print(json.dumps({"stream": response_text[i:i + CHUNK_SIZE]}), flush=True)
            print(json.dumps({"end": True}), flush=True)

        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)
            traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    main()
