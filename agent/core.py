"""Agent core -- factory and execution engine."""
import asyncio
from typing import AsyncIterator, Optional

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from config import settings
from agent.prompts import SYSTEM_PROMPT
from agent.tools import get_all_tools
from agent.tools.browser import set_current_page


def _create_llm():
    """Create the LLM instance based on settings.llm_provider."""
    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )
    else:
        return ChatOpenAI(
            model=settings.model_name,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0,
        )


class AgentSession:
    """Manages a single agent session with its own isolated browser instance."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._agent_graph = None
        self._history: list = []  # 手动管理对话历史，避免 checkpointer 状态异常

    async def start(self) -> None:
        """Initialize Playwright browser and create the LangChain agent."""
        self._playwright = await async_playwright().start()
        launch_args = {"headless": settings.browser_headless}
        if settings.browser_channel:
            launch_args["channel"] = settings.browser_channel
        print(f"[DEBUG] Launching browser: {launch_args}", flush=True)
        self._browser = await self._playwright.chromium.launch(**launch_args)
        print(f"[DEBUG] Browser connected: {self._browser.is_connected()}", flush=True)
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
        )
        self._page = await self._context.new_page()
        print(f"[DEBUG] Page created, is_closed={self._page.is_closed()}", flush=True)

        llm = _create_llm()
        tools = get_all_tools()

        self._agent_graph = create_agent(
            model=llm,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
        )
        print(f"[DEBUG] Agent created with {len(tools)} tools", flush=True)

    async def _ensure_page(self) -> Page:
        """Ensure a working page exists. Recreates browser/page if closed or missing."""
        if self._browser is None or not self._browser.is_connected():
            print("[DEBUG] Browser disconnected, relaunching...", flush=True)
            launch_args = {"headless": settings.browser_headless}
            if settings.browser_channel:
                launch_args["channel"] = settings.browser_channel
            self._browser = await self._playwright.chromium.launch(**launch_args)
        if self._context is None:
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 800},
            )
        if self._page is None or self._page.is_closed():
            print("[DEBUG] Page closed or missing, creating new page...", flush=True)
            self._page = await self._context.new_page()
            print(f"[DEBUG] New page created, title: {await self._page.title()}", flush=True)
        return self._page

    async def run(self, message: str) -> str:
        """Run the agent with a user message and return the final response."""
        if not self._agent_graph:
            raise RuntimeError("Session not started. Call start() first.")

        page = await self._ensure_page()
        set_current_page(page)

        # Build input with full conversation history
        input_messages = [*self._history, {"role": "user", "content": message}]
        try:
            result = await self._agent_graph.ainvoke(
                {"messages": input_messages},
            )
            # Extract the last AI response from messages
            messages = result.get("messages", [])
            final_response = None
            for msg in reversed(messages):
                if hasattr(msg, "content") and msg.type == "ai":
                    content = msg.content
                    if content:
                        final_response = content
                        break

            # Update history: keep only user + assistant turns (not tool messages)
            if final_response:
                self._history.append({"role": "user", "content": message})
                self._history.append({"role": "assistant", "content": final_response})
                # Limit history to last 20 turns to avoid context overflow
                if len(self._history) > 40:
                    self._history = self._history[-40:]
                return final_response
            return "No response generated."
        finally:
            set_current_page(None)

    async def stream(self, message: str) -> AsyncIterator[str]:
        """Run the agent and yield response tokens as they stream in."""
        if not self._agent_graph:
            raise RuntimeError("Session not started. Call start() first.")

        page = await self._ensure_page()
        set_current_page(page)
        print(f"[DEBUG] stream: page ready, url={page.url}", flush=True)

        # Build input with full conversation history
        input_messages = [*self._history, {"role": "user", "content": message}]
        full_response = ""
        try:
            # Use astream with messages mode for token-level streaming
            async for chunk in self._agent_graph.astream(
                {"messages": input_messages},
                stream_mode="messages",
            ):
                # chunk is (message_chunk, metadata) tuple
                if isinstance(chunk, tuple) and len(chunk) >= 1:
                    msg_chunk = chunk[0]
                    if hasattr(msg_chunk, "content") and msg_chunk.content:
                        # Only yield content from AI messages (not tool messages)
                        if hasattr(msg_chunk, "type") and msg_chunk.type == "AIMessageChunk":
                            content = msg_chunk.content
                            if isinstance(content, str) and content:
                                full_response += content
                                yield content
        finally:
            print(f"[DEBUG] stream: done, page is_closed={page.is_closed()}", flush=True)
            # Update history after stream completes
            if full_response:
                self._history.append({"role": "user", "content": message})
                self._history.append({"role": "assistant", "content": full_response})
                if len(self._history) > 40:
                    self._history = self._history[-40:]
            set_current_page(None)

    async def close(self) -> None:
        """Clean up all browser resources."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


async def create_session(session_id: str) -> AgentSession:
    """Create and initialize a new agent session."""
    session = AgentSession(session_id)
    await session.start()
    return session
