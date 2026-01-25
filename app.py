"""
Flask web application for the Brand Boost AI chatbot.
Integrates with the Google ADK agent orchestration system.
"""

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    send_from_directory,
)
from flask_cors import CORS
import os
import sys
from pathlib import Path
import uuid
from dotenv import load_dotenv

# --- ADK imports ---
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

# -------------------------------------------------------------------
# Path + environment setup
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
AGENTS_DIR = BASE_DIR / "agents"

sys.path.insert(0, str(AGENTS_DIR))

load_dotenv(AGENTS_DIR / ".env")

# Import the ADK root agent
from agents.agent import root_agent

# -------------------------------------------------------------------
# Flask app setup
# -------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "dev-secret-key-change-in-production"
)
CORS(app)

# -------------------------------------------------------------------
# ADK Session Service (ONE per app)
# -------------------------------------------------------------------

session_service = InMemorySessionService()

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
async def chat():
    try:
        # Get or create session ID and user ID
        session_id = session.get("session_id")
        user_id = session.get("user_id")

        if not session_id:
            session_id = str(uuid.uuid4())
            session["session_id"] = session_id

        if not user_id:
            user_id = str(uuid.uuid4())
            session["user_id"] = user_id

        # Get user message
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({
                "status": "error",
                "response": "Please provide a message."
            }), 400

        # Convert message to Content object
        message_content = Content(parts=[Part(text=user_message)], role="user")

        # Create session if it doesn't exist
        existing_session = None
        try:
            existing_session = await session_service.get_session(
                app_name="brand_boost_ai",
                user_id=user_id,
                session_id=session_id
            )
        except Exception:
            pass

        if not existing_session:
            await session_service.create_session(
                app_name="brand_boost_ai",
                user_id=user_id,
                session_id=session_id
            )

        # Create runner
        runner = Runner(
            app_name="brand_boost_ai",
            agent=root_agent,
            session_service=session_service,
        )

        # Run agent
        result = runner.run(
            session_id=session_id,
            user_id=user_id,
            new_message=message_content
        )

        # Iterate through events to get final response
        final_response_text = ""
        for event in result:
            if event.is_final_response() and event.content and event.content.parts:
                final_response_text = event.content.parts[0].text

        # Validate response is not empty
        if not final_response_text or not final_response_text.strip():
            app.logger.warning("Agent returned empty response")
            return jsonify({
                "status": "error",
                "response": "We're experiencing technical difficulties at the moment. Please try again in a few moments."
            }), 500

        # Check if response contains image references
        images = extract_image_info(final_response_text)

        return jsonify({
            "status": "success",
            "response": final_response_text,
            "images": images
        })

    except Exception as e:
        app.logger.exception("Chat processing error")
        return jsonify({
            "status": "error",
            "response": "We're experiencing technical difficulties at the moment. Please try again in a few moments."
        }), 500


def extract_image_info(text: str) -> list:
    """Extract recently created images (within last 30 seconds)."""
    import time
    images = []
    artifacts_dir = AGENTS_DIR / "design" / "artifacts"

    if not artifacts_dir.exists():
        return images

    current_time = time.time()
    threshold = 30  # seconds

    # Check all asset directories for recent images
    for asset_dir in artifacts_dir.iterdir():
        if not asset_dir.is_dir():
            continue

        # Get all versions and check modification times
        recent_versions = []
        for version_file in sorted(asset_dir.glob("v*.png")):
            # Check if file was modified recently
            if current_time - version_file.stat().st_mtime <= threshold:
                try:
                    version_num = int(version_file.stem[1:])
                    recent_versions.append({
                        "version": version_num,
                        "url": f"/artifacts/{asset_dir.name}/{version_file.name}",
                        "mtime": version_file.stat().st_mtime
                    })
                except ValueError:
                    continue

        if recent_versions:
            # Sort by modification time to get the latest
            recent_versions.sort(key=lambda x: x["mtime"], reverse=True)
            images.append({
                "name": asset_dir.name,
                "versions": [{"version": v["version"], "url": v["url"]} for v in recent_versions],
                "latest": recent_versions[0]["url"]
            })

    return images


@app.route("/api/artifacts", methods=["GET"])
async def list_artifacts():
    """List all design artifacts."""
    try:
        artifacts_dir = AGENTS_DIR / "design" / "artifacts"

        if not artifacts_dir.exists():
            return jsonify({"artifacts": []})

        artifacts = []
        for asset_dir in artifacts_dir.iterdir():
            if not asset_dir.is_dir():
                continue

            versions = []
            for version_file in sorted(asset_dir.glob("v*.png")):
                try:
                    version_num = int(version_file.stem[1:])
                    versions.append({
                        "version": version_num,
                        "url": f"/artifacts/{asset_dir.name}/{version_file.name}"
                    })
                except ValueError:
                    continue

            if versions:
                artifacts.append({
                    "name": asset_dir.name,
                    "versions": versions,
                    "latest": versions[-1]["url"] if versions else None
                })

        return jsonify({"artifacts": artifacts})

    except Exception as e:
        app.logger.exception("Error listing artifacts")
        return jsonify({"artifacts": []})


@app.route("/artifacts/<path:filename>")
def serve_artifact(filename):
    """Serve design artifact images."""
    artifacts_dir = AGENTS_DIR / "design" / "artifacts"
    return send_from_directory(artifacts_dir, filename)


# -------------------------------------------------------------------
# App entrypoint
# -------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
    )
