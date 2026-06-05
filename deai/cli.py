"""Command-line interface for deai."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .styles import STYLES, pick_style
from .languages.python import humanize_python
from .git_forger import generate_commits, write_forge_script


def _resolve_style(style_arg: str | None, rng):
    if style_arg is None or style_arg == "random":
        return pick_style(rng)
    if style_arg not in STYLES:
        raise SystemExit(
            f"Unknown style '{style_arg}'. Choose from: {', '.join(STYLES.keys())}"
        )
    return STYLES[style_arg]


def main():
    parser = argparse.ArgumentParser(
        prog="deai",
        description="Make AI-generated code look hand-written.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # humanize command
    humanize = sub.add_parser("humanize", help="Humanize source files")
    humanize.add_argument("input", help="Input file or directory")
    humanize.add_argument("-o", "--output", help="Output file or directory")
    humanize.add_argument(
        "--style",
        choices=list(STYLES.keys()) + ["random"],
        default="random",
        help="Developer persona to simulate",
    )
    humanize.add_argument("--seed", type=int, default=None, help="Random seed")
    humanize.add_argument(
        "--in-place", action="store_true", help="Overwrite input files"
    )

    # git forge command
    forge = sub.add_parser("forge-git", help="Generate realistic git commit history")
    forge.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    forge.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    forge.add_argument("--count", type=int, default=30)
    forge.add_argument("--seed", type=int, default=None)
    forge.add_argument("--repo", default=".")
    forge.add_argument("-o", "--output", default="forge_commits.sh")

    args = parser.parse_args()

    if args.command == "humanize":
        import random

        rng = random.Random(args.seed)
        style = _resolve_style(args.style, rng)
        input_path = Path(args.input)

        if input_path.is_file():
            source = input_path.read_text(encoding="utf-8")
            # Language dispatch (only Python today)
            result = humanize_python(source, style, args.seed)
            if args.in_place:
                input_path.write_text(result, encoding="utf-8")
                print(f"Overwritten: {input_path}")
            elif args.output:
                out = Path(args.output)
                out.write_text(result, encoding="utf-8")
                print(f"Written: {out}")
            else:
                print(result)
        elif input_path.is_dir():
            files = list(input_path.rglob("*.py"))
            if not files:
                print("No .py files found.", file=sys.stderr)
                sys.exit(1)
            for f in files:
                # Per-file style if requested random
                file_style = _resolve_style(args.style, rng)
                source = f.read_text(encoding="utf-8")
                result = humanize_python(source, file_style, args.seed)
                if args.in_place:
                    f.write_text(result, encoding="utf-8")
                else:
                    base = Path(args.output) if args.output else Path("deai_output")
                    out = base / f.relative_to(input_path)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(result, encoding="utf-8")
            target = input_path if args.in_place else (args.output or "deai_output")
            print(f"Processed {len(files)} files -> {target}")
        else:
            print(f"Input not found: {input_path}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "forge-git":
        import datetime

        start = datetime.date.fromisoformat(args.start)
        end = datetime.date.fromisoformat(args.end)
        commits = generate_commits(start, end, args.count, args.seed)
        script = write_forge_script(commits, args.output, args.repo)
        print(f"Wrote {len(commits)} forged commits to {script}")


if __name__ == "__main__":
    main()
