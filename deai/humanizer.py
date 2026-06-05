"""Shared utilities for style-driven humanization."""
from __future__ import annotations

import random
from typing import Optional

from .styles import StyleProfile, pick_style


class HumanizerContext:
    """Carries style + RNG through a transformation pipeline."""

    def __init__(self, style: StyleProfile, seed: Optional[int] = None):
        self.style = style
        self.rng = random.Random(seed)

    def should(self, probability: float) -> bool:
        return self.rng.random() < probability

    def choice(self, seq):
        return self.rng.choice(seq)

    def randint(self, a: int, b: int) -> int:
        return self.rng.randint(a, b)

    def human_name(self, category: str) -> str:
        """Pick a name from a category, respecting style."""
        from .languages.python import PYTHON_NAME_POOLS
        pool = PYTHON_NAME_POOLS.get(category, ["x", "y", "z"])
        if self.style.naming_style == "short":
            pool = [p for p in pool if len(p) <= 3] or pool
        elif self.style.naming_style == "verbose":
            pool = [p for p in pool if len(p) >= 4] or pool
        return self.rng.choice(pool)
