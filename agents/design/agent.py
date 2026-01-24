from pathlib import Path

from google.adk import Agent

from agents.design.tools.edit_image import edit_image_tool
from agents.design.tools.create_image import create_image_tool
from agents.design.tools.list_artifacts import list_artifacts_tool

instruction_path = Path(__file__).parent / "prompts/design_prompt.md"
instruction = instruction_path.read_text()


root_agent = Agent(
    name="design_agent",
    model="gemini-2.5-flash",
    instruction=instruction,
    tools=[
        list_artifacts_tool,
        create_image_tool,
        edit_image_tool,
    ],
)