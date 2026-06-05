"""Forge realistic git commit histories for software copyright evidence."""

from __future__ import annotations

import datetime
import random
from pathlib import Path
from typing import List, Optional

COMMIT_POOLS = {
    "feature": [
        "add {thing}",
        "implement {thing}",
        "feat: {thing}",
        "wrote {thing}",
        "build {thing}",
    ],
    "fix": [
        "fix {thing}",
        "fix bug in {thing}",
        "hotfix: {thing}",
        "patch {thing}",
        "bugfix: {thing}",
    ],
    "refactor": [
        "refactor {thing}",
        "cleanup {thing}",
        "rewrite {thing}",
        "simplify {thing}",
    ],
    "docs": [
        "update readme",
        "add comments",
        "document {thing}",
        "clarify {thing}",
        "update docs",
    ],
    "wip": [
        "wip",
        "checkpoint",
        "saving progress",
        "tmp commit",
        "backup",
    ],
    "chore": [
        "update deps",
        "fix typo",
        "formatting",
        "rename {thing}",
        "lint",
    ],
    "test": [
        "add tests for {thing}",
        "fix failing test",
        "coverage",
    ],
}

THINGS = [
    "parser",
    "core logic",
    "api client",
    "auth",
    "utils",
    "config",
    "main loop",
    "error handling",
    "cli",
    "data model",
    "validation",
    "export",
]

WEEKDAY_HOURS = [9, 10, 11, 14, 15, 16, 20, 21, 22, 23]
WEEKEND_HOURS = [13, 14, 15, 20, 21, 22]


def _random_time(rng: random.Random, is_weekend: bool) -> datetime.time:
    hours = WEEKEND_HOURS if is_weekend else WEEKDAY_HOURS
    # 20% chance for very late night
    if rng.random() < 0.2:
        hours = [0, 1, 2, 3]
    hour = rng.choice(hours)
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)
    return datetime.time(hour, minute, second)


def generate_commits(
    start_date: datetime.date,
    end_date: datetime.date,
    count: int = 30,
    seed: Optional[int] = None,
) -> List[dict]:
    """Generate a list of fake commits with realistic timestamps."""
    rng = random.Random(seed)
    total_days = max(1, (end_date - start_date).days)
    step = total_days / max(1, count)

    commits = []
    current = start_date
    for _ in range(count):
        current = min(current, end_date)
        is_weekend = current.weekday() >= 5

        # Skip some weekends, simulate crunch-time before deadline
        if is_weekend and rng.random() < 0.55:
            current += datetime.timedelta(days=max(1, int(step)))
            continue

        t = _random_time(rng, is_weekend)
        dt = datetime.datetime.combine(current, t)

        ctype = rng.choices(
            ["feature", "fix", "refactor", "docs", "wip", "chore", "test"],
            weights=[0.30, 0.22, 0.10, 0.10, 0.12, 0.10, 0.06],
        )[0]
        thing = rng.choice(THINGS)
        msg = rng.choice(COMMIT_POOLS[ctype]).format(thing=thing)

        commits.append(
            {
                "datetime": dt,
                "message": msg,
                "type": ctype,
            }
        )

        # Advance by step with jitter
        jitter = rng.randint(-1, 2)
        current += datetime.timedelta(days=max(1, int(step) + jitter))

    return commits


def write_forge_script(
    commits: List[dict],
    output_path: str = "forge_commits.sh",
    repo_path: str = ".",
) -> str:
    """Write a bash script that replays commits with backdated timestamps."""
    lines = [
        "#!/bin/bash",
        "set -e",
        f'cd "{repo_path}"',
        "",
        "# Make sure repo is initialized",
        "if [ ! -d .git ]; then git init; fi",
        "",
        "# Remove any empty commits from previous runs",
        "",
    ]
    for c in commits:
        iso = c["datetime"].strftime("%Y-%m-%dT%H:%M:%S")
        msg = c["message"].replace('"', '\\"')
        lines.append(
            f'GIT_AUTHOR_DATE="{iso}" GIT_COMMITTER_DATE="{iso}" '
            f'git commit --allow-empty -m "{msg}"'
        )
    lines.append("")

    path = Path(output_path)
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path.absolute())


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Forge realistic git history.")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--repo", default=".")
    parser.add_argument("-o", "--output", default="forge_commits.sh")
    args = parser.parse_args()

    start = datetime.date.fromisoformat(args.start)
    end = datetime.date.fromisoformat(args.end)
    commits = generate_commits(start, end, args.count, args.seed)
    script = write_forge_script(commits, args.output, args.repo)
    print(f"Wrote {len(commits)} forged commits to {script}")
