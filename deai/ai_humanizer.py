"""AI-powered code humanizer using LLM APIs (DeepSeek, OpenAI, Claude)."""
from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI

from .styles import StyleProfile

STYLE_PROMPTS = {
    "veteran": (
        "You are a 10-year veteran developer who hates meetings and types fast. "
        "Rewrite this code to look like you wrote it in a hurry: use short variable names (i, j, k, tmp, buf), "
        "remove all docstrings and type hints, add occasional swear words or frustration comments like '# ugh' or '# fix this garbage', "
        "use tight spacing, inconsistent quotes (mix ' and \"), and make it look pragmatic but slightly messy."
    ),
    "junior": (
        "You are a first-year intern who just discovered StackOverflow. "
        "Rewrite this code to look like a junior wrote it: overly verbose variable names, excessive comments explaining obvious things, "
        "keep type hints, add TODO comments like '# TODO: understand this', occasional typos, and a naive enthusiasm."
    ),
    "hacker": (
        "You are a sleep-deprived hacker at 3AM fueled by caffeine. "
        "Rewrite this code to look like a rushed prototype: mixed naming styles, curse words in comments, "
        "inconsistent spacing, 2-space indent, random temp variables, and a 'works on my machine' vibe."
    ),
    "perfectionist": (
        "You are a developer obsessed with types and dataclasses. "
        "Rewrite this code keeping all type hints but making it look slightly over-engineered: verbose names, "
        "consider refactoring comments, excessive use of typing imports, and a 'this could be generalized' attitude."
    ),
    "copypaster": (
        "You glued this code together from 4 different StackOverflow answers. "
        "Rewrite it to look copied: inconsistent naming conventions, mixed quote styles, comments like '# from old repo', "
        "different formatting in different sections, and a general feeling of duct tape."
    ),
}


def _build_system_prompt(style: StyleProfile) -> str:
    base = STYLE_PROMPTS.get(
        style.name,
        "Rewrite this code to look like it was written by a human developer, not AI. "
        "Vary naming conventions, add human-style comments, use inconsistent formatting, and avoid perfect patterns.",
    )
    return (
        f"{base}\n\n"
        "IMPORTANT RULES:\n"
        "1. ONLY return the rewritten code, no explanations before or after\n"
        "2. Preserve the original functionality exactly\n"
        "3. Do not add markdown code fences\n"
        "4. Make it look authentically human-written"
    )


def humanize_with_ai(
    source: str,
    style: StyleProfile,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """Humanize code using an LLM API."""
    api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("No API key provided. Set OPENAI_API_KEY or DEEPSEEK_API_KEY, or pass api_key.")

    base_url = base_url or os.environ.get("OPENAI_BASE_URL")
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _build_system_prompt(style)},
            {"role": "user", "content": f"Rewrite this Python code:\n\n{source}"},
        ],
        temperature=0.9,
        max_tokens=4096,
    )

    result = response.choices[0].message.content or source
    # Strip markdown fences if the model added them
    result = result.strip()
    if result.startswith("```python"):
        result = result[9:]
    if result.startswith("```"):
        result = result[3:]
    if result.endswith("```"):
        result = result[:-3]
    return result.strip()
