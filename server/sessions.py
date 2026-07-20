"""Session lifecycle management with idle-time cleanup."""
import asyncio
import time
import uuid
from typing import Dict, Optional

from agent.core import AgentSession, create_session


class SessionManager:
    """Tracks active agent sessions and cleans up idle ones."""

    def __init__(self, idle_timeout: int = 1800):
        self._sessions: Dict[str, AgentSession] = {}
        self._last_activity: Dict[str, float] = {}
        self._idle_timeout = idle_timeout
        self._cleanup_task: Optional[asyncio.Task] = None

    async def get_or_create(self, session_id: Optional[str] = None) -> tuple[str, AgentSession]:
        """Return an existing session or create a new one."""
        if session_id and session_id in self._sessions:
            self._last_activity[session_id] = time.time()
            return session_id, self._sessions[session_id]

        new_id = session_id or str(uuid.uuid4())[:8]
        session = await create_session(new_id)
        self._sessions[new_id] = session
        self._last_activity[new_id] = time.time()
        return new_id, session

    def touch(self, session_id: str) -> None:
        """Refresh the last-activity timestamp."""
        if session_id in self._last_activity:
            self._last_activity[session_id] = time.time()

    async def remove(self, session_id: str) -> None:
        """Close and remove a session."""
        if session_id in self._sessions:
            session = self._sessions.pop(session_id)
            await session.close()
            self._last_activity.pop(session_id, None)

    async def cleanup_idle(self) -> None:
        """Close sessions that exceeded the idle timeout."""
        now = time.time()
        idle = [sid for sid, last in self._last_activity.items() if now - last > self._idle_timeout]
        for sid in idle:
            await self.remove(sid)

    async def start_cleanup_loop(self) -> None:
        """Launch periodic cleanup (every 5 minutes)."""
        async def _loop():
            while True:
                await asyncio.sleep(300)
                await self.cleanup_idle()

        self._cleanup_task = asyncio.create_task(_loop())

    async def shutdown(self) -> None:
        """Close all sessions and stop the cleanup loop."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        for sid in list(self._sessions.keys()):
            await self.remove(sid)


session_manager = SessionManager()
