from pathlib import Path

from google.adk.agents import Agent

# Load instruction from content_prompt.md
instruction_path = Path(__file__).parent / "content_prompt.md"
instruction = instruction_path.read_text()

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A Social Media Content Agent with expertise in brand communication, promotion, and ethical storytelling. Creates high-impact, platform-specific content that balances clarity, emotional resonance, and strategic intent.',
    instruction=instruction,
)
