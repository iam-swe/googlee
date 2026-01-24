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
# In-memory stores (UI-only)
# -------------------------------------------------------------------

conversations: dict[str, list] = {}

# -------------------------------------------------------------------
# ADK Session Service (ONE per app)
# -------------------------------------------------------------------

session_service = InMemorySessionService()

# -------------------------------------------------------------------
# Helper: normalize ADK output
# -------------------------------------------------------------------

def normalize_adk_result(result) -> str:
    """Convert ADK runner output (string / generator / message) into text."""
    if isinstance(result, str):
        return result

    if hasattr(result, "__iter__"):
        parts = []
        for item in result:
            if isinstance(item, str):
                parts.append(item)
            elif hasattr(item, "text"):
                parts.append(item.text)
            else:
                parts.append(str(item))
        return "".join(parts)

    if hasattr(result, "text"):
        return result.text

    return str(result)

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        # --------------------------------------------------------------
        # Flask session
        # --------------------------------------------------------------

        session_id = session.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            session["session_id"] = session_id

        # --------------------------------------------------------------
        # Request parsing
        # --------------------------------------------------------------

        data = request.get_json(force=True, silent=True) or {}
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({
                "status": "error",
                "response": "Please provide a message."
            }), 400

        # --------------------------------------------------------------
        # UI conversation history
        # --------------------------------------------------------------

        conversations.setdefault(session_id, []).append({
            "role": "user",
            "content": user_message
        })

        # --------------------------------------------------------------
        # ADK Runner invocation (CORRECT FOR YOUR VERSION)
        # --------------------------------------------------------------

        runner = Runner(
            app_name="brand_boost_ai",
            agent=root_agent,
            session_service=session_service,
        )

        # IMPORTANT: positional args only
        result = runner.run(session_id=session_id,user_id=str(uuid.uuid4()),new_message=user_message)

        agent_response = normalize_adk_result(result)

        # --------------------------------------------------------------
        # Store assistant response
        # --------------------------------------------------------------

        conversations[session_id].append({
            "role": "assistant",
            "content": agent_response
        })

        return jsonify({
            "status": "success",
            "response": agent_response
        })

    except Exception as e:
        app.logger.exception("Chat processing error")
        return jsonify({
            "status": "error",
            "response": f"Sorry, I encountered an error: {str(e)}"
        }), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    session_id = session.get("session_id")
    return jsonify({
        "history": conversations.get(session_id, [])
    })


@app.route("/api/clear", methods=["POST"])
def clear_history():
    session_id = session.get("session_id")
    if session_id:
        conversations.pop(session_id, None)
        session_service.delete_session(session_id)
    return jsonify({"status": "success"})


@app.route("/api/artifacts", methods=["GET"])
def get_artifacts():
    try:
        artifacts_dir = AGENTS_DIR / "design" / "artifacts"
        if not artifacts_dir.exists():
            return jsonify({"artifacts": []})

        artifacts = []

        for asset_dir in artifacts_dir.iterdir():
            if not asset_dir.is_dir():
                continue

            versions = []
            latest_version = None
            latest_path = None

            for version_file in asset_dir.glob("v*.png"):
                try:
                    version_num = int(version_file.stem[1:])
                except ValueError:
                    continue

                versions.append(version_num)

                if latest_version is None or version_num > latest_version:
                    latest_version = version_num
                    latest_path = f"/artifacts/{asset_dir.name}/{version_file.name}"

            if versions:
                artifacts.append({
                    "name": asset_dir.name,
                    "versions": sorted(versions),
                    "latest": latest_path
                })

        return jsonify({"artifacts": artifacts})

    except Exception:
        app.logger.exception("Artifact fetch error")
        return jsonify({"artifacts": []})


@app.route("/artifacts/<path:filename>")
def serve_artifact(filename):
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
