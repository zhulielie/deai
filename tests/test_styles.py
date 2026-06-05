"""Tests for style profile definitions."""
import random

import pytest

from deai.styles import StyleProfile, STYLES, pick_style


def test_all_styles_are_valid():
    for name, profile in STYLES.items():
        assert profile.name == name
        assert 0.0 <= profile.comment_density <= 1.0
        assert 0.0 <= profile.typo_rate <= 1.0
        assert profile.indent_size > 0


def test_pick_style_random():
    rng = random.Random(42)
    style = pick_style(rng)
    assert style.name in STYLES


def test_pick_style_allowed():
    rng = random.Random(42)
    allowed = ["veteran", "junior"]
    for _ in range(20):
        style = pick_style(rng, allowed=allowed)
        assert style.name in allowed


def test_pick_style_empty_allowed_fallback():
    rng = random.Random(42)
    style = pick_style(rng, allowed=[])
    assert style.name in STYLES
