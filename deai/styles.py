"""Style profiles that simulate real human developer fingerprints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class StyleProfile:
    """A synthetic human developer fingerprint."""

    # Required identity
    name: str
    description: str

    # Naming
    naming_style: str  # short | mixed | verbose | hungarian

    # Comments
    comment_density: float  # 0.0 .. 1.0
    typo_rate: float  # 0.0 .. 1.0
    use_docstrings: bool
    docstring_verbosity: str  # minimal | normal | excessive

    # Syntax preferences
    use_type_hints: bool
    prefer_fstrings: bool
    prefer_list_comp: bool

    # Formatting
    bracket_spacing: str  # tight | loose | mixed
    operator_spacing: str  # tight | loose | mixed
    indent_style: str  # spaces | tabs
    indent_size: int
    blank_lines: tuple  # (min, max)
    line_length_preference: int

    # Behaviour flags
    temp_variable_rate: float  # how often to split one assign into two
    redundant_compare_rate: float  # x -> x == True, is None -> == None
    private_prefix_rate: float  # prepend _ to functions

    # Optional vocabulary injected into comments
    curse_words: List[str] = field(default_factory=list)
    todo_phrases: List[str] = field(default_factory=list)
    hack_phrases: List[str] = field(default_factory=list)
    confessions: List[str] = field(default_factory=list)

    # Optional naming decorations
    name_prefixes: List[str] = field(default_factory=list)
    name_suffixes: List[str] = field(default_factory=list)


def pick_style(rng, allowed: List[str] | None = None) -> StyleProfile:
    """Pick a random style profile."""
    pool = {k: v for k, v in STYLES.items() if allowed is None or k in allowed}
    if not pool:
        pool = STYLES
    key = rng.choice(list(pool.keys()))
    return pool[key]


STYLES = {
    "veteran": StyleProfile(
        name="veteran",
        description="10-year dev who hates meetings and types fast.",
        naming_style="short",
        comment_density=0.05,
        typo_rate=0.08,
        use_docstrings=False,
        docstring_verbosity="minimal",
        use_type_hints=False,
        prefer_fstrings=False,
        prefer_list_comp=False,
        bracket_spacing="tight",
        operator_spacing="tight",
        indent_style="spaces",
        indent_size=4,
        blank_lines=(0, 1),
        line_length_preference=100,
        curse_words=["ugh", "wtf", "damn", "sigh", "crap"],
        todo_phrases=["fix this garbage", "revisit", "dont forget", "later"],
        hack_phrases=["this is cursed", "works on my machine", "pray"],
        confessions=["not proud of this", "legacy reasons", "dont ask"],
        temp_variable_rate=0.05,
        redundant_compare_rate=0.10,
        private_prefix_rate=0.15,
    ),
    "junior": StyleProfile(
        name="junior",
        description="First internship. Over-explains and copies StackOverflow.",
        naming_style="verbose",
        comment_density=0.70,
        typo_rate=0.12,
        use_docstrings=True,
        docstring_verbosity="excessive",
        use_type_hints=True,
        prefer_fstrings=True,
        prefer_list_comp=True,
        bracket_spacing="loose",
        operator_spacing="loose",
        indent_style="spaces",
        indent_size=4,
        blank_lines=(1, 3),
        line_length_preference=80,
        curse_words=[],
        todo_phrases=[
            "I am not sure about this part",
            "need to ask mentor",
            "TODO: understand this",
            "TODO: improve",
        ],
        hack_phrases=[
            "temporary solution",
            "not best practice",
            "will improve later",
        ],
        confessions=[
            "copied from tutorial",
            "might be wrong",
            "seems to work",
        ],
        temp_variable_rate=0.25,
        redundant_compare_rate=0.20,
        private_prefix_rate=0.05,
    ),
    "hacker": StyleProfile(
        name="hacker",
        description="Late-night caffeine-fueled prototype builder.",
        naming_style="mixed",
        name_prefixes=["my", "raw", "tmp", "old"],
        name_suffixes=["2", "_v2", "_fix", "_new"],
        comment_density=0.20,
        typo_rate=0.20,
        use_docstrings=False,
        docstring_verbosity="minimal",
        use_type_hints=False,
        prefer_fstrings=True,
        prefer_list_comp=True,
        bracket_spacing="mixed",
        operator_spacing="mixed",
        indent_style="spaces",
        indent_size=2,
        blank_lines=(0, 2),
        line_length_preference=120,
        curse_words=["shit", "fck", "damn"],
        todo_phrases=["fixme", "hacked", "kludge", "band-aid"],
        hack_phrases=["magic number", "brute force", "good enough"],
        confessions=["sleep deprived", "3am commit", "no tests"],
        temp_variable_rate=0.15,
        redundant_compare_rate=0.15,
        private_prefix_rate=0.10,
    ),
    "perfectionist": StyleProfile(
        name="perfectionist",
        description="Loves typing, dataclasses, and 100% mypy coverage.",
        naming_style="verbose",
        comment_density=0.30,
        typo_rate=0.02,
        use_docstrings=True,
        docstring_verbosity="normal",
        use_type_hints=True,
        prefer_fstrings=True,
        prefer_list_comp=True,
        bracket_spacing="loose",
        operator_spacing="loose",
        indent_style="spaces",
        indent_size=4,
        blank_lines=(1, 2),
        line_length_preference=88,
        curse_words=["sigh"],
        todo_phrases=["consider refactoring", "extract method", "add unit test"],
        hack_phrases=["could be generalized", "suboptimal"],
        confessions=["overengineered", "premature abstraction"],
        temp_variable_rate=0.10,
        redundant_compare_rate=0.05,
        private_prefix_rate=0.20,
    ),
    "copypaster": StyleProfile(
        name="copypaster",
        description="Glued together from 4 different projects.",
        naming_style="mixed",
        comment_density=0.40,
        typo_rate=0.10,
        use_docstrings=True,
        docstring_verbosity="normal",
        use_type_hints=True,
        prefer_fstrings=False,
        prefer_list_comp=False,
        bracket_spacing="mixed",
        operator_spacing="mixed",
        indent_style="mixed",
        indent_size=4,
        blank_lines=(0, 3),
        line_length_preference=90,
        curse_words=["ugly"],
        todo_phrases=["from old repo", "adapted", "see original"],
        hack_phrases=["copied", " pasted ", "borrowed"],
        confessions=["should credit source", "legacy"],
        temp_variable_rate=0.20,
        redundant_compare_rate=0.25,
        private_prefix_rate=0.10,
    ),
}
