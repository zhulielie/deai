"""Web UI for deai — dual-engine (AST + AI) with ZIP batch support."""
from __future__ import annotations

import io
import os
import random
import sys
import zipfile
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file,
)

from deai.ai_humanizer import humanize_with_ai
from deai.languages.python import humanize_python
from deai.styles import STYLES, pick_style

app = Flask(__name__)


def _resolve_style(style_name: str, seed: int | None):
    rng = random.Random(seed)
    if style_name == "random" or style_name not in STYLES:
        return pick_style(rng)
    return STYLES[style_name]


@app.route("/")
def index():
    return render_template("index.html", styles=list(STYLES.keys()))


@app.route("/api/humanize", methods=["POST"])
def api_humanize():
    data = request.get_json(force=True)
    source = data.get("source", "")
    style_name = data.get("style", "random")
    seed = data.get("seed")
    engine = data.get("engine", "ast")

    if seed is not None:
        try:
            seed = int(seed)
        except (ValueError, TypeError):
            seed = None

    style = _resolve_style(style_name, seed)

    try:
        if engine == "ai":
            result = humanize_with_ai(
                source,
                style,
                api_key=data.get("api_key"),
                base_url=data.get("base_url"),
                model=data.get("model"),
            )
        else:
            result = humanize_python(source, style, seed)
        return jsonify({"ok": True, "result": result, "style_used": style.name})
    except SyntaxError as e:
        return jsonify({"ok": False, "error": f"Syntax error: {e}"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/batch", methods=["POST"])
def api_batch():
    """Batch process a ZIP upload."""
    uploaded = request.files.get("zip")
    if not uploaded:
        return jsonify({"ok": False, "error": "No ZIP file uploaded"}), 400

    style_name = request.form.get("style", "random")
    seed = request.form.get("seed")
    engine = request.form.get("engine", "ast")

    if seed:
        try:
            seed = int(seed)
        except (ValueError, TypeError):
            seed = None

    style = _resolve_style(style_name, seed)

    # Read uploaded zip
    in_buffer = io.BytesIO(uploaded.read())
    out_buffer = io.BytesIO()

    results = []
    errors = []

    try:
        with zipfile.ZipFile(in_buffer, "r") as zin:
            with zipfile.ZipFile(out_buffer, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.namelist():
                    data = zin.read(item)
                    if not item.endswith(".py") or "__pycache__" in item:
                        zout.writestr(item, data)
                        continue

                    try:
                        source = data.decode("utf-8")
                        if engine == "ai":
                            result = humanize_with_ai(
                                source,
                                style,
                                api_key=request.form.get("api_key") or None,
                                base_url=request.form.get("base_url") or None,
                                model=request.form.get("model") or None,
                            )
                        else:
                            result = humanize_python(source, style, seed)
                        zout.writestr(item, result.encode("utf-8"))
                        results.append(item)
                    except Exception as e:
                        errors.append({"file": item, "error": str(e)})
                        zout.writestr(item, data)
    except zipfile.BadZipFile:
        return jsonify({"ok": False, "error": "Invalid ZIP file"}), 400

    out_buffer.seek(0)
    return send_file(
        out_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="deai_output.zip",
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
