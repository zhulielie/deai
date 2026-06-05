"""Tests for git history forger."""

import datetime
from pathlib import Path

from deai.git_forger import generate_commits, write_forge_script


def test_generate_commits_count():
    start = datetime.date(2024, 1, 1)
    end = datetime.date(2024, 1, 31)
    commits = generate_commits(start, end, count=10, seed=42)
    # generate_commits may skip weekends, so count can be <= requested
    assert 0 < len(commits) <= 10


def test_generate_commits_date_range():
    start = datetime.date(2024, 1, 1)
    end = datetime.date(2024, 3, 31)
    commits = generate_commits(start, end, count=50, seed=42)
    for c in commits:
        assert start <= c["datetime"].date() <= end


def test_generate_commits_types():
    start = datetime.date(2024, 1, 1)
    end = datetime.date(2024, 1, 31)
    commits = generate_commits(start, end, count=30, seed=42)
    valid_types = {"feature", "fix", "refactor", "docs", "wip", "chore", "test"}
    for c in commits:
        assert c["type"] in valid_types
        assert c["message"]
        assert isinstance(c["datetime"], datetime.datetime)


def test_generate_commits_deterministic_with_seed():
    start = datetime.date(2024, 1, 1)
    end = datetime.date(2024, 1, 31)
    c1 = generate_commits(start, end, count=10, seed=99)
    c2 = generate_commits(start, end, count=10, seed=99)
    assert [x["message"] for x in c1] == [x["message"] for x in c2]


def test_write_forge_script(tmp_path):
    start = datetime.date(2024, 1, 1)
    end = datetime.date(2024, 1, 10)
    commits = generate_commits(start, end, count=5, seed=1)
    out = tmp_path / "forge.sh"
    path = write_forge_script(commits, str(out), repo_path=".")
    assert Path(path).exists()
    content = out.read_text(encoding="utf-8")
    assert "#!/bin/bash" in content
    assert "git commit --allow-empty" in content
    for c in commits:
        assert c["message"] in content
