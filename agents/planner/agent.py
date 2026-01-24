from pathlib import Path

from google.adk.agents import Agent

# Load instruction from planner_prompt.md
instruction_path = Path(__file__).parent / "planner_prompt.md"
instruction = instruction_path.read_text()

root_agent = Agent(
    model='gemini-2.5-flash',
    name='planner_agent',
    description='A Marketing Strategy Planner Agent that creates comprehensive, actionable marketing plans across Instagram, Threads, LinkedIn, and X (Twitter). Provides separate text and image ideas for each platform and seeks user confirmation before implementation.',
    instruction=instruction,
)

