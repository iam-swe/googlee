from pathlib import Path

project_root = Path(__file__).resolve().parent.parent

def load_prompt(name: str) -> str:
    prompt_path = project_root / "prompts" / name
    print(prompt_path)
    return prompt_path.read_text(encoding="utf-8")

def generate_output_path(name: str) -> Path:
    asset_dir = project_root / "artifacts" / name
    asset_dir.mkdir(parents=True, exist_ok=True)

    versions = [
        int(p.stem[1:]) for p in asset_dir.glob("v*.png")
        if p.stem[1:].isdigit()
    ]
    next_version = max(versions, default=0) + 1

    return asset_dir / f"v{next_version}.png"

def get_latest_image(asset_dir: Path) -> Path:
    versions = [
        int(p.stem[1:]) for p in asset_dir.glob("v*.png")
        if p.stem[1:].isdigit()
    ]
    if not versions:
        raise RuntimeError("No existing versions found")

    return asset_dir / f"v{max(versions)}.png"


