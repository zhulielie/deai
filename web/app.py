"""Simple web UI for deai."""
from __future__ import annotations

import random
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, jsonify, render_template, request

from deai.languages.python import humanize_python
from deai.styles import STYLES, pick_style

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", styles=list(STYLES.keys()))


@app.route("/api/humanize", methods=["POST"])
def api_humanize():
    data = request.get_json(force=True)
    source = data.get("source", "")
    style_name = data.get("style", "random")
    seed = data.get("seed")

    if seed is not None:
        try:
            seed = int(seed)
        except (ValueError, TypeError):
            seed = None

    rng = random.Random(seed)
    if style_name == "random" or style_name not in STYLES:
        style = pick_style(rng)
    else:
        style = STYLES[style_name]

    try:
        result = humanize_python(source, style, seed)
        return jsonify({"ok": True, "result": result, "style_used": style.name})
    except SyntaxError as e:
        return jsonify({"ok": False, "error": f"Syntax error: {e}"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
