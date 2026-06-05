"""Tests for HumanizerContext utilities."""
import random

from deai.humanizer import HumanizerContext
from deai.styles import STYLES


def test_should_deterministic_with_seed():
    style = STYLES["veteran"]
    ctx = HumanizerContext(style, seed=123)
    results = [ctx.should(0.5) for _ in range(10)]
    ctx2 = HumanizerContext(style, seed=123)
    results2 = [ctx2.should(0.5) for _ in range(10)]
    assert results == results2


def test_choice_and_randint():
    style = STYLES["veteran"]
    ctx = HumanizerContext(style, seed=1)
    assert ctx.choice(["a", "b", "c"]) in {"a", "b", "c"}
    assert 1 <= ctx.randint(1, 10) <= 10


def test_human_name_respects_naming_style():
    rng = random.Random(1)
    short_style = STYLES["veteran"]  # naming_style == "short"
    verbose_style = STYLES["junior"]  # naming_style == "verbose"

    short_ctx = HumanizerContext(short_style, seed=1)
    name = short_ctx.human_name("index")
    assert len(name) <= 3 or name in ("idx", "pos", "ii", "jj", "kk", "nn")

    verbose_ctx = HumanizerContext(verbose_style, seed=1)
    name2 = verbose_ctx.human_name("index")
    assert len(name2) >= 3 or name2 in ("idx", "pos", "counter", "holder")
