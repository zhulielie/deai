"""Web UI for deai — dual-engine (AST + AI) with ZIP batch support."""
from __future__ import annotations

import io
import os
import random
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
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


def _humanize_source(source: str, style, engine: str, seed, config_dict):
    if engine == "ai":
        return humanize_with_ai(
            source,
            style,
            api_key=config_dict.get("api_key") or None,
            base_url=config_dict.get("base_url") or None,
            model=config_dict.get("model") or None,
            provider=config_dict.get("provider") or None,
        )
    return humanize_python(source, style, seed)


def _process_folder(source_dir: Path, target_dir: Path, style, engine: str, seed, config_dict):
    """Process all .py files in source_dir, write results to target_dir."""
    processed = 0
    skipped = 0
    errors = []

    for py_file in source_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            skipped += 1
            continue
        rel = py_file.relative_to(source_dir)
        out_file = target_dir / rel
        out_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            source = py_file.read_text(encoding="utf-8")
            result = _humanize_source(source, style, engine, seed, config_dict)
            out_file.write_text(result, encoding="utf-8")
            processed += 1
        except Exception as e:
            errors.append({"file": str(rel), "error": str(e)})
            try:
                out_file.write_text(py_file.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass

    return processed, skipped, errors


@app.route("/api/local", methods=["POST"])
def api_local():
    """Process a local source (folder or ZIP) → target (folder or ZIP or in-place)."""
    data = request.get_json(force=True)
    source_path = data.get("source", "").strip()
    target_path = data.get("target", "").strip()

    if not source_path:
        return jsonify({"ok": False, "error": "No source path provided"}), 400

    source_obj = Path(source_path)
    if not source_obj.exists():
        return jsonify({"ok": False, "error": f"Source not found: {source_path}"}), 400

    style_name = data.get("style", "random")
    seed = data.get("seed")
    engine = data.get("engine", "ast")

    if seed is not None:
        try:
            seed = int(seed)
        except (ValueError, TypeError):
            seed = None

    style = _resolve_style(style_name, seed)
    config = {
        "api_key": data.get("api_key"),
        "base_url": data.get("base_url"),
        "model": data.get("model"),
        "provider": data.get("provider"),
    }

    is_source_zip = source_obj.is_file() and source_path.lower().endswith(".zip")

    # Determine target
    in_place = not target_path
    if in_place:
        target_obj = source_obj
    else:
        target_obj = Path(target_path)
        target_obj.parent.mkdir(parents=True, exist_ok=True)

    # Work directory
    if is_source_zip:
        # Extract to temp, process, then re-pack or copy
        with tempfile.TemporaryDirectory() as tmpdir:
            extract_dir = Path(tmpdir) / "extracted"
            extract_dir.mkdir()
            with zipfile.ZipFile(source_obj, "r") as zin:
                zin.extractall(extract_dir)

            # Determine output dir inside temp
            out_dir = Path(tmpdir) / "output"
            out_dir.mkdir()

            processed, skipped, errors = _process_folder(extract_dir, out_dir, style, engine, seed, config)

            if in_place or (target_path and target_path.lower().endswith(".zip")):
                # Output as ZIP
                out_zip = target_obj if in_place else target_obj
                with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zout:
                    for f in out_dir.rglob("*"):
                        if f.is_file():
                            arcname = f.relative_to(out_dir)
                            zout.write(f, arcname)
                return jsonify({
                    "ok": True,
                    "processed": processed,
                    "skipped": skipped,
                    "errors": errors,
                    "target": str(out_zip),
                    "in_place": in_place,
                })
            else:
                # Output as folder
                if target_obj.exists() and target_obj.is_dir():
                    shutil.rmtree(target_obj)
                shutil.copytree(out_dir, target_obj)
                return jsonify({
                    "ok": True,
                    "processed": processed,
                    "skipped": skipped,
                    "errors": errors,
                    "target": str(target_obj),
                    "in_place": in_place,
                })
    else:
        # Source is folder
        if not source_obj.is_dir():
            return jsonify({"ok": False, "error": f"Source is not a folder or ZIP: {source_path}"}), 400

        if in_place:
            target_dir = source_obj
        else:
            target_dir = target_obj
            target_dir.mkdir(parents=True, exist_ok=True)

        processed, skipped, errors = _process_folder(source_obj, target_dir, style, engine, seed, config)

        return jsonify({
            "ok": True,
            "processed": processed,
            "skipped": skipped,
            "errors": errors,
            "target": str(target_dir),
            "in_place": in_place,
        })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
