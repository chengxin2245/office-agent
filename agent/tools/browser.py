"""Browser automation tools using Playwright."""
import base64
import sys
from typing import Optional

from langchain_core.tools import tool
from playwright.async_api import Page

_current_page: Optional["Page"] = None


def set_current_page(page: Optional["Page"]) -> None:
    global _current_page
    _current_page = page
    print(f"[DEBUG] set_current_page: {page is not None}", flush=True)


def get_current_page() -> Optional["Page"]:
    result = _current_page
    print(f"[DEBUG] get_current_page: {result is not None}", flush=True)
    return result


@tool
async def navigate(url: str) -> str:
    """Navigate the browser to a specific URL.

    Args:
        url: The full URL to navigate to (e.g., https://example.com).
    """
    page = get_current_page()
    if not page:
        return "Error: No browser page is active."
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return f"Navigated to: {url}\nPage title: {await page.title()}"
    except Exception as e:
        return f"Error navigating to {url}: {str(e)}"


@tool
async def click(selector: str) -> str:
    """Click on an element on the current page.

    Args:
        selector: CSS selector for the element (e.g., '#submit', '.btn-primary', 'button').
    """
    page = get_current_page()
    if not page:
        return "Error: No browser page is active."
    try:
        await page.click(selector, timeout=10000)
        return f"Clicked element: {selector}"
    except Exception as e:
        return f"Error clicking '{selector}': {str(e)}"


@tool
async def type_text(selector: str, text: str) -> str:
    """Type text into an input element on the page.

    Args:
        selector: CSS selector for the input element.
        text: The text to type.
    """
    page = get_current_page()
    if not page:
        return "Error: No browser page is active."
    try:
        await page.fill(selector, text, timeout=10000)
        return f"Typed '{text}' into '{selector}'"
    except Exception as e:
        return f"Error typing into '{selector}': {str(e)}"


@tool
async def screenshot() -> str:
    """Take a screenshot of the current page for visual inspection."""
    page = get_current_page()
    if not page:
        return "Error: No browser page is active."
    try:
        screenshot_bytes = await page.screenshot(type="png", full_page=False)
        b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        url = await page.url
        title = await page.title()
        return (
            f"Screenshot captured.\n"
            f"Current URL: {url}\n"
            f"Page title: {title}\n"
            f"Viewport: {page.viewport_size}\n"
            f"[screenshot_base64:{b64[:200]}...]"
        )
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"


@tool
async def extract_text(selector: str) -> str:
    """Extract text content from a specific element on the page.

    Args:
        selector: CSS selector for the target element.
    """
    page = get_current_page()
    if not page:
        return "Error: No browser page is active."
    try:
        element = page.locator(selector).first
        text = await element.text_content()
        return f"Text from '{selector}':\n{text}"
    except Exception as e:
        return f"Error extracting text from '{selector}': {str(e)}"


@tool
async def extract_all_text() -> str:
    """Extract all visible text content from the current page. Truncates at 8000 chars."""
    page = get_current_page()
    if not page:
        return "Error: No browser page is active."
    try:
        text = await page.locator("body").inner_text()
        if len(text) > 8000:
            text = text[:8000] + "\n... [truncated]"
        return f"Page text content:\n{text}"
    except Exception as e:
        return f"Error extracting page text: {str(e)}"


@tool
async def wait(seconds: float) -> str:
    """Wait for a specified number of seconds.

    Args:
        seconds: Number of seconds to wait.
    """
    import asyncio
    await asyncio.sleep(seconds)
    return f"Waited {seconds} seconds."


@tool
async def scroll_down() -> str:
    """Scroll down the current page by one viewport height."""
    page = get_current_page()
    if not page:
        return "Error: No browser page is active."
    try:
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        return "Scrolled down one viewport."
    except Exception as e:
        return f"Error scrolling: {str(e)}"


@tool
async def get_current_url() -> str:
    """Get the current page URL."""
    page = get_current_page()
    if not page:
        return "Error: No browser page is active."
    try:
        return f"Current URL: {await page.url}"
    except Exception as e:
        return f"Error getting URL: {str(e)}"


@tool
async def press_key(key: str) -> str:
    """Press a keyboard key on the current page.

    Args:
        key: Key name (e.g., 'Enter', 'Escape', 'Tab', 'ArrowDown').
    """
    page = get_current_page()
    if not page:
        return "Error: No browser page is active."
    try:
        await page.keyboard.press(key)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Error pressing key '{key}': {str(e)}"


def get_browser_tools():
    """Return all browser automation tools."""
    return [
        navigate,
        click,
        type_text,
        screenshot,
        extract_text,
        extract_all_text,
        wait,
        scroll_down,
        get_current_url,
        press_key,
    ]
