"""CLI test script to verify the agent works locally.

Usage:
    python test_agent.py "Navigate to https://example.com and tell me the page title"
    python test_agent.py                           # interactive mode
"""
import asyncio
import sys

# Add project root to path for direct execution
sys.path.insert(0, r"C:\Users\86130\Documents\Codex\2026-07-19\ni-h\office-agent")

from agent.core import create_session


async def main():
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = input("请输入任务: ")

    print("\n正在创建浏览器会话...")
    session = await create_session("cli-test")

    try:
        print(f"执行任务: {task}\n")
        print("=" * 60)
        async for token in session.stream(task):
            print(token, end="", flush=True)
        print("\n" + "=" * 60)
        print("\n任务执行完成。浏览器窗口将自动关闭。")
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
