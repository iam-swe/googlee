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

# Apply nest_asyncio to allow nested event loops (helps with Flask + async MCP tools)
import nest_asyncio
nest_asyncio.apply()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

BASE_DIR = Path(__file__).parent
AGENTS_DIR = BASE_DIR / "agents"

sys.path.insert(0, str(AGENTS_DIR))

load_dotenv(AGENTS_DIR / ".env")

from agents.agent import root_agent


app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "dev-secret-key-change-in-production"
)
CORS(app)

session_service = InMemorySessionService()

@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
async def chat():
    try:
        session_id, user_id = get_or_create_session_ids()

        user_message = get_user_message()
        if user_message is None:
            return jsonify({
                "status": "error",
                "response": "Please provide a message."
            }), 400

        await ensure_session_exists(session_id, user_id)

        result = await run_agent(session_id, user_id, user_message)
        response_text = extract_final_response(result)

        if not response_text or not response_text.strip():
            app.logger.warning("Agent returned empty response")
            return create_error_response()

        images = extract_image_info(response_text)
        return create_success_response(response_text, images)

    except Exception as e:
        app.logger.exception("Chat processing error")
        return create_error_response()

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


@app.route("/api/new-session", methods=["POST"])
def new_session():
    """Create a new chat session."""
    session["session_id"] = str(uuid.uuid4())
    session["user_id"] = str(uuid.uuid4())
    return jsonify({"status": "success"})


def get_or_create_session_ids():
    session_id = session.get("session_id")
    user_id = session.get("user_id")

    if not session_id:
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id

    if not user_id:
        user_id = str(uuid.uuid4())
        session["user_id"] = user_id

    return session_id, user_id


def get_user_message():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return None

    return user_message


async def ensure_session_exists(session_id, user_id):
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


async def run_agent(session_id, user_id, user_message):
    message_content = Content(parts=[Part(text=user_message)], role="user")

    runner = Runner(
        app_name="brand_boost_ai",
        agent=root_agent,
        session_service=session_service,
    )

    events = []
    async for event in runner.run_async(
        session_id=session_id,
        user_id=user_id,
        new_message=message_content
    ):
        events.append(event)

    return events


def extract_final_response(result):
    for event in result:
        if event.is_final_response() and event.content and event.content.parts:
            return event.content.parts[0].text
    return ""


def extract_image_info(text: str) -> list:
    import time
    images = []
    artifacts_dir = AGENTS_DIR / "design" / "artifacts"

    if not artifacts_dir.exists():
        return images

    current_time = time.time()
    threshold = 30

    for asset_dir in artifacts_dir.iterdir():
        if not asset_dir.is_dir():
            continue

        recent_versions = []
        for version_file in sorted(asset_dir.glob("v*.png")):
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
            recent_versions.sort(key=lambda x: x["mtime"], reverse=True)
            images.append({
                "name": asset_dir.name,
                "versions": [{"version": v["version"], "url": v["url"]} for v in recent_versions],
                "latest": recent_versions[0]["url"]
            })

    return images


def create_error_response():
    return jsonify({
        "status": "error",
        "response": "We're experiencing technical difficulties at the moment. Please try again in a few moments."
    }), 500


def create_success_response(response_text, images):
    return jsonify({
        "status": "success",
        "response": response_text,
        "images": images
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
    )
