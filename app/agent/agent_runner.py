import asyncio
import json
import sys
import traceback
from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from app.agent.graph import agent_graph
from app.agent.memory import (
    load_short_term,
    new_session_id,
    save_message,
    save_to_long_term,
    search_long_term,
)
from app.agent.prompt import build_system_prompt
from app.core.database import get_db_context
from app.mcp.client import MCPClient

CHUNK_SIZE = 20


# ── Guardrails ───────────────────────

def is_greeting(text: str) -> bool:
    return text.lower().strip() in {"hi", "hello", "hey", "good morning", "good evening", "good afternoon"}


def is_weak_response(text: str) -> bool:
    if len(text.strip()) < 15:
        return True
    weak = ["i'm not sure", "i am not sure", "i don't know", "i do not know",
            "as an ai", "cannot answer", "not sure", "i cannot"]
    return any(p in text.lower() for p in weak)


def add_stronger_prompt(messages: list) -> list:
    messages.insert(1, SystemMessage(content=(
        "Answer confidently and directly using the tool data you retrieved. "
        "Do not say you are unsure. Give specific numbers and dates."
    )))
    return messages


# ── Core agentic loop ─────────────────────────────────────────

async def run_agent(user_message: str, user_id: int, session_id: str) -> str:
    """
    Full agentic loop:
      LangGraph decides → MCP executes tools → LangGraph continues → answer
    """
    mcp = MCPClient()

    async with get_db_context() as db:
        # 1. Short-term memory
        history = await load_short_term(db, user_id, session_id)

        # 2. Long-term memory
        long_term = await search_long_term(user_id, user_message, n_results=3)

        # 3. System prompt (includes long-term context if any)
        system_content = build_system_prompt(
            user_name="User",
            user_id=user_id,
            current_date=date.today().isoformat(),
        )
        if long_term:
            system_content += "\n\n---\nRelevant context from past conversations:\n" + \
                              "\n".join(f"• {s}" for s in long_term)

        # 4. Build messages
        messages = [SystemMessage(content=system_content)] + history + [HumanMessage(content=user_message)]

        # 5. Agentic tool loop
        max_iterations = 6
        for _ in range(max_iterations):
            result   = agent_graph.invoke({"messages": messages})
            messages = result["messages"]
            last     = messages[-1]

            # No tool calls → LLM gave a final answer
            if not getattr(last, "tool_calls", None):
                break

            # Tool calls → execute via MCP, inject results, loop back
            tool_messages = []
            for call in last.tool_calls:
                tool_name = call["name"]
                tool_args = dict(call["args"])

                # Always inject user_id for subscription tools
                if "user_id" not in tool_args:
                    tool_args["user_id"] = user_id

                try:
                    result_data = mcp.call_tool(tool_name, tool_args)
                    content = json.dumps(result_data, default=str) if not isinstance(result_data, str) else result_data
                except Exception as exc:
                    content = json.dumps({"error": str(exc)})

                tool_messages.append(
                    ToolMessage(content=content, tool_call_id=call["id"])
                )

            messages = messages + tool_messages

        response_text = last.content or "I couldn't generate a response."

        # 6. Guardrail retry
        if not is_greeting(user_message) and is_weak_response(response_text):
            messages = add_stronger_prompt(messages)
            result        = agent_graph.invoke({"messages": messages})
            response_text = result["messages"][-1].content or response_text

        # 7. Persist to memory
        await save_message(db, user_id, session_id, "human", user_message)
        await save_message(db, user_id, session_id, "ai",    response_text)

        summary = f"User: {user_message[:150]}\nAssistant: {response_text[:250]}"
        await save_to_long_term(user_id, session_id, summary)

    return response_text


# ── Stdin/stdout loop (same pattern as your agent_runner.py) ──

async def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            data         = json.loads(line)
            user_message = data.get("message", "").strip()
            user_id      = data.get("user_id", 0)
            session_id   = data.get("session_id") or new_session_id()

            response_text = await run_agent(user_message, user_id, session_id)

            # Stream response in chunks
            for i in range(0, len(response_text), CHUNK_SIZE):
                chunk = response_text[i:i + CHUNK_SIZE]
                print(json.dumps({"stream": chunk, "session_id": session_id}), flush=True)

            print(json.dumps({"end": True, "session_id": session_id}), flush=True)

        except Exception as exc:
            print(json.dumps({"error": str(exc)}), flush=True)
            traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
