from pathlib import Path

from google import genai
import os
from dotenv import load_dotenv
from PIL import Image
from google.adk.tools import  FunctionTool

from utils.artifact_utils import generate_output_path, get_latest_image, load_prompt

load_dotenv()

def edit_image(name: str, design_instructions: str):
    """
    Edits the latest image for an existing asset using design instructions.

    Returns:
        None: Saves the edited image as a new version under the asset’s artifacts directory.
    """
    project_root = Path(__file__).resolve().parent.parent
    asset_dir = project_root / "artifacts" / name

    latest_image_path = get_latest_image(asset_dir)
    base_image = Image.open(latest_image_path)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not found")

    client = genai.Client(api_key=api_key)

    nano_edit_prompt = load_prompt("nano_edit_prompt.md")
    final_prompt = f"{nano_edit_prompt}\n{design_instructions}"

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

edit_image_tool  = FunctionTool(
    func=edit_image,
)