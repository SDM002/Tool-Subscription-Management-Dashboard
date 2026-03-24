"""
app/agent/assistant_service.py  [NEW]

Core AI assistant service.

Flow for each user message:
1. Load short-term memory (last N messages from SQL)
2. Search long-term memory (ChromaDB similarity) for relevant context
3. Build message list: [system_prompt, long_term_context, history, user_msg]
4. Call Anthropic Claude with tool definitions
5. If tool_use blocks are returned → dispatch tools → append results → re-call
6. Extract final text reply
7. Persist user + assistant messages to SQL (short-term)
8. Persist assistant reply to ChromaDB (long-term) for future retrieval

Data isolation: user_id scopes all DB queries and ChromaDB collections.
"""

import json
import logging
from datetime import date

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.memory import (
    generate_session_id,
    load_short_term,
    save_message,
    save_to_long_term,
    search_long_term,
)
from app.agent.prompt import build_system_prompt
from app.agent.tools_registry import TOOL_DEFINITIONS, dispatch_tool
from app.core.config import settings

logger = logging.getLogger(__name__)

# Anthropic client — reused across requests
_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


class AssistantService:

    async def chat(
        self,
        db: AsyncSession,
        user_id: int,
        user_name: str,
        user_email: str,
        user_message: str,
        session_id: str | None = None,
    ) -> tuple[str, str]:
        """
        Process a user message and return (reply, session_id).

        Args:
            db: Async DB session (used for tool calls + memory)
            user_id: Authenticated user ID
            user_name / user_email: For personalized system prompt
            user_message: The user's input text
            session_id: Optional; a new one is created if None

        Returns:
            (assistant_reply: str, session_id: str)
        """
        if not settings.anthropic_api_key:
            return (
                "⚠️ The AI assistant is not configured. "
                "Please set ANTHROPIC_API_KEY in your .env file.",
                session_id or generate_session_id(),
            )

        if session_id is None:
            session_id = generate_session_id()

        # ── 1. Short-term memory ──────────────────────────────
        history = await load_short_term(db, user_id, session_id)

        # ── 2. Long-term memory search ────────────────────────
        long_term_snippets = await search_long_term(
            user_id=user_id,
            query=user_message,
            n_results=3,
        )

        # ── 3. Build system prompt ────────────────────────────
        system_prompt = build_system_prompt(
            user_name=user_name,
            user_email=user_email,
            current_date=date.today().isoformat(),
        )

        if long_term_snippets:
            context_block = "\n\n---\nRelevant context from past conversations:\n" + "\n".join(
                f"• {s}" for s in long_term_snippets
            )
            system_prompt += context_block

        # ── 4. Build messages list ────────────────────────────
        messages = list(history)  # copy short-term history
        messages.append({"role": "user", "content": user_message})

        # ── 5. LLM call with tool loop ────────────────────────
        client = _get_client()
        reply = await self._run_tool_loop(
            client=client,
            system_prompt=system_prompt,
            messages=messages,
            db=db,
            user_id=user_id,
        )

        # ── 6. Persist to short-term memory ──────────────────
        await save_message(db, user_id, session_id, "user", user_message)
        await save_message(db, user_id, session_id, "assistant", reply)

        # ── 7. Persist summary to long-term memory ────────────
        # Store a compact summary of the exchange for future semantic retrieval
        summary = f"User asked: {user_message[:200]}\nAssistant replied: {reply[:300]}"
        await save_to_long_term(
            user_id=user_id,
            session_id=session_id,
            content=summary,
            metadata={"type": "exchange"},
        )

        return reply, session_id

    async def _run_tool_loop(
        self,
        client: anthropic.AsyncAnthropic,
        system_prompt: str,
        messages: list[dict],
        db: AsyncSession,
        user_id: int,
        max_iterations: int = 5,
    ) -> str:
        """
        Agentic tool loop:
        Keep calling the LLM until it returns a final text response
        (no more tool_use blocks) or we hit max_iterations.
        """
        current_messages = list(messages)

        for iteration in range(max_iterations):
            response = await client.messages.create(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
                system=system_prompt,
                tools=TOOL_DEFINITIONS,
                messages=current_messages,
            )

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Extract text from the last response
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                # Process all tool calls in this response
                assistant_content = response.content
                tool_results = []

                for block in assistant_content:
                    if block.type == "tool_use":
                        logger.info(
                            "Tool call: %s with input %s",
                            block.name,
                            json.dumps(block.input)[:200],
                        )
                        result_str = await dispatch_tool(
                            tool_name=block.name,
                            tool_input=block.input,
                            db=db,
                            user_id=user_id,
                        )
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_str,
                            }
                        )

                # Append assistant response + tool results to message history
                current_messages.append(
                    {"role": "assistant", "content": assistant_content}
                )
                current_messages.append(
                    {"role": "user", "content": tool_results}
                )
                continue

            # Unexpected stop reason — return whatever text we have
            return self._extract_text(response)

        return "I'm sorry, I couldn't complete that request. Please try again."

    def _extract_text(self, response: anthropic.types.Message) -> str:
        """Extract plain text from the Anthropic response."""
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts).strip() or "I couldn't generate a response."


assistant_service = AssistantService()
