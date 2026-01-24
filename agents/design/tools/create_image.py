from google import genai
import os
from dotenv import load_dotenv
from google.adk.tools import  FunctionTool
from agents.design.utils.artifact_utils import load_prompt, generate_output_path

load_dotenv()


def create_image(name: str, design_instructions: str):
    """
        Generates a new image for a given asset using design instructions.

        Returns:
        None: Saves the generated image as a new version under the asset’s artifacts directory.
    """
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    nano_create_prompt = load_prompt("nano_create_prompt.md")
    final_prompt = f"""{nano_create_prompt}

    {design_instructions}
    """

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
            image.save(str(output_path))


create_image_tool = FunctionTool(func=create_image)
