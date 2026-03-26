import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send a message to the AI assistant and get a response.

    - Requires a valid JWT token (Bearer auth)
    - session_id is optional; if omitted a new session is created
    - The agent uses the user's subscription data via MCP tools
    - Short-term memory (SQL) + long-term memory (ChromaDB) are both used
    """
    # Deferred imports: LangChain / ChromaDB are only loaded when the
    # first chat request arrives, not at application startup.
    # This keeps startup fast and avoids import-time crashes if heavy
    # ML packages are being installed separately.
    from app.agent.agent_runner import run_agent

    session_id = payload.session_id or uuid.uuid4().hex

    try:
        reply = await run_agent(
            user_message=payload.message,
            user_id=current_user.id,
            session_id=session_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(exc)}")

    return ChatResponse(session_id=session_id, reply=reply)