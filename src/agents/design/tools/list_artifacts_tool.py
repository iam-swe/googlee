from pathlib import Path
from google.adk.tools import tool

@tool(
    name="load_artifacts",
    description="List all image assets and their available versions."
)
def load_artifacts() -> dict:
    project_root = Path(__file__).resolve().parent.parent
    artifacts_dir = project_root / "artifacts"

    if not artifacts_dir.exists():
        return {}

    summary: dict[str, list[str]] = {}

    for asset_dir in artifacts_dir.iterdir():
        if not asset_dir.is_dir():
            continue

        versions = []
        for file in asset_dir.glob("v*.png"):
            stem = file.stem
            if stem[1:].isdigit():
                versions.append(stem)

        if versions:
            summary[asset_dir.name] = sorted(
                versions, key=lambda v: int(v[1:])
            )

    return summary

print(load_artifacts())
