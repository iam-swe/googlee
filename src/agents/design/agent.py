from pathlib import Path

from google.adk import Agent
from google.adk.tools.load_artifacts_tool import load_artifacts_tool

from tools.edit_image import edit_image_tool
from tools.generate_image import generate_image_tool

instruction_path = Path(__file__).parent / "prompts/design_prompt.md"
instruction = instruction_path.read_text()


root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction=instruction,
    tools=[
        load_artifacts_tool,
        generate_image_tool,
        edit_image_tool,
    ],
)