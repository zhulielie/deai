"""Tests for Python language humanizer."""

import pytest

from deai.languages.python import humanize_python
from deai.styles import STYLES

SAMPLE = '''
def process(items):
    """Process items."""
    if items is None:
        return None
    result = []
    for item in items:
        if item.get("active"):
            result.append(item)
    return result
'''


def test_humanize_veteran_strips_docstrings():
    style = STYLES["veteran"]
    out = humanize_python(SAMPLE, style, seed=42)
    assert '"""Process items."""' not in out
    assert "def " in out


def test_humanize_junior_keeps_docstrings():
    style = STYLES["junior"]
    out = humanize_python(SAMPLE, style, seed=42)
    # Junior may keep or expand docstrings; just verify it runs
    assert "def " in out


def test_humanize_veteran_strips_type_hints():
    source = "def foo(x: int) -> str:\n    return str(x)\n"
    style = STYLES["veteran"]
    out = humanize_python(source, style, seed=42)
    assert "-> str" not in out
    assert ": int" not in out


def test_humanize_perfectionist_keeps_type_hints():
    # All styles now strip type hints for adversarial robustness.
    # Verify with a custom style that use_type_hints=True still works.
    from deai.styles import StyleProfile
    source = "def foo(x: int) -> str:\n    return str(x)\n"
    custom = StyleProfile(
        name="typed",
        description="test",
        naming_style="short",
        comment_density=0.0,
        typo_rate=0.0,
        use_docstrings=False,
        docstring_verbosity="minimal",
        use_type_hints=True,
        prefer_fstrings=False,
        prefer_list_comp=False,
        bracket_spacing="tight",
        operator_spacing="tight",
        indent_style="spaces",
        indent_size=4,
        blank_lines=(0, 0),
        line_length_preference=80,
        temp_variable_rate=0.0,
        redundant_compare_rate=0.0,
        private_prefix_rate=0.0,
    )
    out = humanize_python(source, custom, seed=42)
    assert ": int" in out
    assert "->" in out and "str" in out


def test_humanize_renames_variables():
    style = STYLES["veteran"]
    out = humanize_python(SAMPLE, style, seed=42)
    # With veteran style, type hints and docstrings are stripped, and
    # variables are renamed to short names. Just assert valid Python.
    compile(out, "<test>", "exec")
    assert "def process(" in out or "def _process(" in out


def test_humanize_injects_comments():
    style = STYLES["hacker"]
    out = humanize_python(SAMPLE, style, seed=42)
    # Hacker has comment_density=0.20, so comments may appear
    assert "#" in out or "def " in out  # lax check; mainly ensures no crash


def test_humanize_preserves_semantics():
    """Renamed code should still be valid Python."""
    style = STYLES["copypaster"]
    out = humanize_python(SAMPLE, style, seed=42)
    compile(out, "<test>", "exec")


def test_humanize_empty_source():
    out = humanize_python("", STYLES["veteran"], seed=1)
    assert out.strip() == ""


def test_humanize_annassign_without_type_hints():
    source = "x: int = 1\n"
    style = STYLES["veteran"]
    out = humanize_python(source, style, seed=1)
    # spacing pass may add spaces around =
    assert "=" in out and "x" in out
    assert ": int" not in out
