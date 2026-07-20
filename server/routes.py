from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.sessions import session_manager

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the agent and get a response."""
    try:
        sid, session = await session_manager.get_or_create(request.session_id)
        session_manager.touch(sid)
        response = await session.run(request.message)
        return ChatResponse(session_id=sid, response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Close and remove a session."""
    await session_manager.remove(session_id)
    return {"status": "ok", "session_id": session_id}


@router.get("/health")
async def health():
    return {"status": "ok"}
