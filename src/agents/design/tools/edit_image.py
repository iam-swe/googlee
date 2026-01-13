from pathlib import Path

from google import genai
import os
from dotenv import load_dotenv
from PIL import Image

from src.agents.design.utils.artifact_utils import load_prompt, generate_output_path

load_dotenv()

def get_latest_image(asset_dir: Path) -> Path:
    versions = [
        int(p.stem[1:]) for p in asset_dir.glob("v*.png")
        if p.stem[1:].isdigit()
    ]
    if not versions:
        raise RuntimeError("No existing versions found")

    return asset_dir / f"v{max(versions)}.png"

def edit_image(name: str, design_instructions: str):
    project_root = Path(__file__).resolve().parent.parent
    asset_dir = project_root / "artifacts" / name

    latest_image_path = get_latest_image(asset_dir)
    print("Latest image: ",latest_image_path)
    output_path = generate_output_path(name)
    print("Output path: ", output_path)
    base_image = Image.open(latest_image_path)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not found")

    client = genai.Client(api_key=api_key)

    nano_edit_prompt = load_prompt("nano_edit_prompt.md")
    final_prompt = f"{nano_edit_prompt}\n{design_instructions}"
    print(final_prompt)
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[
            base_image,
            final_prompt
        ],
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image = part.as_image()
            output_path = generate_output_path(name)
            image.save(str(output_path))
            print(f" Image saved to {output_path}")


# PROJECT_ROOT = Path(__file__).resolve().parent.parent
# PROMPTS_DIR = PROJECT_ROOT / "prompts"
#
# path = PROMPTS_DIR / "sample_design_edit_prompt.md"
# edit_image("home_bakery",path.read_text(encoding="utf-8"))