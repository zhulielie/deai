# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

Install in editable mode with dev dependencies:
```bash
pip install -e ".[dev]"
```

Run the CLI:
```bash
python -m deai humanize <input> [-o <output>] [--style <style>] [--seed <n>]
python -m deai forge-git --start <YYYY-MM-DD> --end <YYYY-MM-DD> [--count <n>]
```

Lint and type-check:
```bash
black deai/
mypy deai/
```

Run tests:
```bash
pytest
```

There are currently no test files in the repo. When adding tests, place them in a `tests/` directory at the repository root.

## Architecture Overview

**deai** is a Python CLI tool with two subcommands: `humanize` (transform code to look hand-written) and `forge-git` (generate a realistic backdated commit history script).

### Humanization Pipeline (`deai humanize`)

The pipeline is language-specific. Only Python is implemented today.

1. **Language dispatch** — `cli.py` calls `languages.python.humanize_python(source, style, seed)`.
2. **AST transformation** — `_StyleTransformer` renames identifiers, strips type hints/docstrings, splits assignments with meaningless temporaries, and injects redundant comparisons (`is None` → `== None`, bare names → `== True`).
3. **Post-processing** — after `ast.unparse`, the source passes through string-level transforms:
   - `_add_comments` — injects todo/hack/confession comments after function defs based on `StyleProfile.comment_density`.
   - `_randomize_quotes` — flips `"` ↔ `'` on string literals via the `tokenize` module.
   - `_messy_spacing` — randomly alters whitespace around operators.
   - `_extra_newlines` — sporadically inserts blank lines.

The `HumanizerContext` class (`humanizer.py`) wraps a `StyleProfile` and `random.Random` instance and provides helpers (`should`, `choice`, `human_name`) used across the pipeline.

### Style Profiles (`styles.py`)

`StyleProfile` is a flat dataclass that encodes a synthetic developer fingerprint: naming style, comment density, typo rate, docstring/type-hint preferences, bracket/operator spacing, indent rules, and vocabulary pools (curse words, todo phrases, etc.).

Five personas are predefined in `STYLES`: `veteran`, `junior`, `hacker`, `perfectionist`, `copypaster`. The CLI accepts `--style random` to draw one per file.

### Git Forger (`git_forger.py`)

`generate_commits(start, end, count, seed)` produces a list of commit dicts with realistic timestamps (weekday vs. weekend hours, late-night spikes, jittered dates). `write_forge_script` emits a bash script that replays them with `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE`.

### Extension Points

- **New language** — add a module under `deai/languages/` exposing a `humanize_<lang>(source, style, seed) -> str` function, then wire it into `cli.py`.
- **New persona** — add a `StyleProfile` instance to `STYLES` in `styles.py`.
- **New AST transform** — add a `visit_*` method to `_StyleTransformer` in `languages/python.py`.
- **New post-processing pass** — add a `_<name>(source, style, rng) -> str` helper in `languages/python.py` and call it from `humanize_python`.

## Project Layout

- `deai/cli.py` — argparse entry point
- `deai/styles.py` — `StyleProfile` definitions
- `deai/humanizer.py` — `HumanizerContext`
- `deai/languages/python.py` — Python AST transformer + post-processing passes
- `deai/git_forger.py` — commit history generator
- `pyproject.toml` — setuptools build config; dev extras are `pytest`, `black`, `mypy`
