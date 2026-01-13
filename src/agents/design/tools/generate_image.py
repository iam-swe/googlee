from pathlib import Path

from google import genai
import os
from dotenv import load_dotenv

load_dotenv()


def load_nano_base_prompt() -> str:
    project_root = Path(__file__).resolve().parent.parent
    prompt_path = project_root / "prompts" / "nano_base_prompt.md"

    return prompt_path.read_text(encoding="utf-8")

def generate_output_path(name: str) -> str:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    asset_dir = PROJECT_ROOT / "artifacts" / name
    asset_dir.mkdir(parents=True, exist_ok=True)

    existing_versions = sorted(asset_dir.glob("v*.png"))
    next_version = len(existing_versions) + 1

    output_path = asset_dir / f"v{next_version}.png"
    return str(output_path)

def generate_image(name: str, design_instructions: str):
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    nano_base_prompt = load_nano_base_prompt()
    final_prompt = f"""{nano_base_prompt}

    {design_instructions}
    """
    print(final_prompt)
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[final_prompt],
    )

    for part in response.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = part.as_image()
            output_path = generate_output_path(name)
            print(f" Image will be saved to {output_path}")
            image.save(output_path)