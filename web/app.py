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
                provider=data.get("provider"),
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
    """Batch process a ZIP upload or multiple files from folder picker."""
    style_name = request.form.get("style", "random")
    seed = request.form.get("seed")
    engine = request.form.get("engine", "ast")

    if seed:
        try:
            seed = int(seed)
        except (ValueError, TypeError):
            seed = None

    style = _resolve_style(style_name, seed)
    out_buffer = io.BytesIO()

    uploaded = request.files.get("zip")
    files = request.files.getlist("files[]")

    try:
        with zipfile.ZipFile(out_buffer, "w", zipfile.ZIP_DEFLATED) as zout:
            if uploaded:
                # ZIP upload path
                with zipfile.ZipFile(io.BytesIO(uploaded.read()), "r") as zin:
                    for item in zin.namelist():
                        data = zin.read(item)
                        if not item.endswith(".py") or "__pycache__" in item:
                            zout.writestr(item, data)
                            continue
                        try:
                            source = data.decode("utf-8")
                            result = _humanize_source(source, style, engine, seed, request.form)
                            zout.writestr(item, result.encode("utf-8"))
                        except Exception as e:
                            zout.writestr(item, data)
            elif files:
                # Folder picker path
                for f in files:
                    if not f.filename.endswith(".py") or "__pycache__" in f.filename:
                        zout.writestr(f.filename, f.read())
                        continue
                    try:
                        source = f.read().decode("utf-8")
                        result = _humanize_source(source, style, engine, seed, request.form)
                        zout.writestr(f.filename, result.encode("utf-8"))
                    except Exception as e:
                        f.seek(0)
                        zout.writestr(f.filename, f.read())
            else:
                return jsonify({"ok": False, "error": "No ZIP file or folder files uploaded"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    out_buffer.seek(0)
    return send_file(
        out_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="deai_output.zip",
    )


def _humanize_source(source: str, style, engine: str, seed, form):
    if engine == "ai":
        return humanize_with_ai(
            source,
            style,
            api_key=form.get("api_key") or None,
            base_url=form.get("base_url") or None,
            model=form.get("model") or None,
            provider=form.get("provider") or None,
        )
    return humanize_python(source, style, seed)


@app.route("/api/local", methods=["POST"])
def api_local():
    """Process a local directory — write results back to disk (in-place or to target dir)."""
    data = request.get_json(force=True)
    source_path = data.get("source", "").strip()
    target_path = data.get("target", "").strip()

    if not source_path:
        return jsonify({"ok": False, "error": "No source path provided"}), 400

    source_obj = Path(source_path)
    if not source_obj.exists():
        return jsonify({"ok": False, "error": f"Source not found: {source_path}"}), 400
    if not source_obj.is_dir():
        return jsonify({"ok": False, "error": f"Not a directory: {source_path}"}), 400

    style_name = data.get("style", "random")
    seed = data.get("seed")
    engine = data.get("engine", "ast")

    if seed is not None:
        try:
            seed = int(seed)
        except (ValueError, TypeError):
            seed = None

    style = _resolve_style(style_name, seed)

    # Determine target
    in_place = not target_path
    target_obj = source_obj if in_place else Path(target_path)
    if not in_place:
        target_obj.mkdir(parents=True, exist_ok=True)

    processed = 0
    skipped = 0
    errors = []

    for py_file in source_obj.rglob("*.py"):
        if "__pycache__" in str(py_file):
            skipped += 1
            continue
        rel = py_file.relative_to(source_obj)
        out_file = target_obj / rel
        if not in_place:
            out_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            source = py_file.read_text(encoding="utf-8")
            if engine == "ai":
                result = humanize_with_ai(
                    source,
                    style,
                    api_key=data.get("api_key") or None,
                    base_url=data.get("base_url") or None,
                    model=data.get("model") or None,
                    provider=data.get("provider") or None,
                )
            else:
                result = humanize_python(source, style, seed)
            out_file.write_text(result, encoding="utf-8")
            processed += 1
        except Exception as e:
            errors.append({"file": str(rel), "error": str(e)})
            if not in_place:
                try:
                    out_file.write_text(py_file.read_text(encoding="utf-8"), encoding="utf-8")
                except Exception:
                    pass

    return jsonify({
        "ok": True,
        "processed": processed,
        "skipped": skipped,
        "errors": errors,
        "target": str(target_obj),
        "in_place": in_place,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
