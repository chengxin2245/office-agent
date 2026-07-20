"""Chainlit chat UI for the office automation agent."""
import chainlit as cl

from agent.core import create_session


@cl.on_chat_start
async def on_chat_start():
    """Initialize a new agent session when a chat begins."""
    session = await create_session(cl.user_session.get("id") or "default")
    cl.user_session.set("agent_session", session)

    await cl.Message(
        content="你好！我是办公自动化助手，可以帮你操作浏览器完成各种网页任务。请告诉我你需要做什么？"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages and stream agent responses."""
    session = cl.user_session.get("agent_session")
    if not session:
        await cl.Message(content="会话未初始化，请刷新页面。").send()
        return

    msg = cl.Message(content="")
    await msg.send()

    try:
        async for token in session.stream(message.content):
            await msg.stream_token(token)
        await msg.update()
    except Exception as e:
        await cl.Message(content=f"执行出错: {str(e)}").send()


@cl.on_chat_end
async def on_chat_end():
    """Clean up browser resources when chat ends."""
    session = cl.user_session.get("agent_session")
    if session:
        await session.close()
