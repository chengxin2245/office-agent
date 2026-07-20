from agent.tools.browser import get_browser_tools
from agent.tools.utils import get_utility_tools


def get_all_tools():
    """Return all available tools for the agent."""
    return get_browser_tools() + get_utility_tools()
