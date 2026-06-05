"""Adversarial test: verify deai beats detect-ai on all detection rules."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# Allow importing detect-ai rules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "antibody" / "detect-ai"))

from detect_ai.rules.python.naming import NamingRule
from detect_ai.rules.python.docstrings import DocstringsRule
from detect_ai.rules.python.type_hints import TypeHintsRule
from detect_ai.rules.python.syntax_preferences import SyntaxPreferenceRule
from detect_ai.rules.python.comments import CommentsRule
from detect_ai.rules.python.formatting import FormattingRule
from detect_ai.rules.python.complexity import ComplexityRule

from deai.languages.python import humanize_python
from deai.styles import STYLES

AI_CODE = '''\
from typing import Optional, List, Dict

def process_user_data(user_list: List[Dict[str, any]], result_dict: Dict, recursive: bool = True) -> Optional[List[Dict]]:
    \"\"\"Process user data and return active users.\n\n    Args:\n        user_list: List of user dictionaries.\n        result_dict: Dictionary to store results.\n        recursive: Whether to process recursively.\n\n    Returns:\n        List of active user dictionaries or None.\n    \"\"\"
    if user_list is None:
        return None
    active_users = []
    for user_obj in user_list:
        if not user_obj.get("is_active"):
            continue
        user_id = user_obj["id"]
        user_name = user_obj['name']
        user_email = user_obj["email"]
        row = {"id": user_id, "name": user_name, 'email': user_email, 'status': 'active'}
        active_users.append(row)
    if recursive:
        print(f'Processed {len(active_users)} users')
    return active_users
'''


def _run_rules(source: str, path: str = "test.py"):
    tree = ast.parse(source)
    rules = [
        NamingRule(),
        DocstringsRule(),
        TypeHintsRule(),
        SyntaxPreferenceRule(),
        CommentsRule(),
        FormattingRule(),
        ComplexityRule(),
    ]
    results = {}
    total = 0.0
    total_weight = 0.0
    for r in rules:
        res = r.analyze(source, tree, path)
        results[res.rule_name] = res
        total += res.weighted_score
        total_weight += res.weight
    overall = total / total_weight if total_weight else 0.0
    return results, overall


def test_adversarial_beats_detect_ai():
    """deai must push detect-ai overall score below 20 (human level)."""
    print("\n=== BEFORE deai ===")
    before_results, before_overall = _run_rules(AI_CODE)
    for name, res in before_results.items():
        print(f"  {name:20s} {res.score:6.1f}  {res.message}")
    print(f"  {'OVERALL':20s} {before_overall:6.1f}")

    for style_name, style in STYLES.items():
        humanized = humanize_python(AI_CODE, style, seed=42)
        print(f"\n=== AFTER deai (style={style_name}) ===")
        after_results, after_overall = _run_rules(humanized)
        for name, res in after_results.items():
            print(f"  {name:20s} {res.score:6.1f}  {res.message}")
        print(f"  {'OVERALL':20s} {after_overall:6.1f}")

        assert after_overall <= 30, (
            f"style={style_name} still scores {after_overall:.1f}, target <=30"
        )


if __name__ == "__main__":
    test_adversarial_beats_detect_ai()
