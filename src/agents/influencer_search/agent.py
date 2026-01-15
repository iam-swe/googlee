import os
from pathlib import Path

from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

instruction_path = Path(__file__).parent / "influencer_search_prompt.md"
instruction = instruction_path.read_text()

firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")

root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    instruction=instruction,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPServerParams(
                url=f"https://mcp.firecrawl.dev/{firecrawl_api_key}/v2/mcp",
            ),
        )
    ],
)