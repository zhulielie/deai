# ⚔️ deai — AI Code Humanizer

> **Turn AI-written code into human-looking code.**  
> Bypass AI detection, style fingerprinting, and copyright scanners.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-22%2F22-brightgreen.svg)](https://github.com/zhuli/deai/actions)
[![VS Code](https://img.shields.io/badge/VS%20Code-Extension-blueviolet.svg)](./vscode-extension)
[![Web UI](https://img.shields.io/badge/Web-UI-orange.svg)](./web)

---

## 🎯 One Command, Zero AI Fingerprints

Modern AI coding assistants leave **detectable fingerprints**:

| AI Fingerprint | Human Counterpart |
|----------------|-------------------|
| Perfect docstrings on every function | Missing or one-liner docs |
| `is None` everywhere | `== None` mixed in |
| 100% f-strings | `.format()` and `%` still around |
| List comprehensions | Explicit `for` + `append` loops |
| Consistent spacing | Random tight/loose operators |
| Descriptive names like `processed_user_data_list` | `tmp`, `buf`, `i`, `seq` |

**deai** strips these fingerprints — not by obfuscating logic, but by rewriting the *surface style* through AST transforms + LLM rewriting.

---

## 🛡️ Proven: Beats detect-ai on All 7 Rules

We built **[detect-ai](https://github.com/zhuli/detect-ai)** (the antagonist) to test deai. Here are the numbers:

| detect-ai Rule | AI Code Score | After deai | Δ |
|----------------|--------------|------------|---|
| **naming** | 85.0 | **20.0** | -77% |
| **docstrings** | 100.0 | **30.0** | -70% |
| **type_hints** | 95.0 | **35.0** | -63% |
| **syntax_preferences** | 85.0 | **25.0** | -71% |
| **comments** | 40.0 | **15~30** | -25~63% |
| **formatting** | 45.0 | **25~40** | -11~44% |
| **complexity** | 35.0 | **35.0** | — |
| **OVERALL** | **71.6** | **26~30** | **-58%** |

All 5 personas pass the scanner at **≤30** (`uncertain` / `likely_human` territory).

---

## 📸 Before vs After

### Input (Typical AI Output)

```python
from typing import Optional, List, Dict

def process_user_data(
    user_list: List[Dict[str, any]],
    result_dict: Dict,
    recursive: bool = True
) -> Optional[List[Dict]]:
    """Process user data and return active users.

    Args:
        user_list: List of user dictionaries.
        result_dict: Dictionary to store results.
        recursive: Whether to process recursively.

    Returns:
        List of active user dictionaries or None.
    """
    if user_list is None:
        return None

    active_users = []
    for user_obj in user_list:
        if not user_obj.get("is_active"):
            continue
        user_id = user_obj["id"]
        user_name = user_obj['name']
        user_email = user_obj["email"]
        row = {
            "id": user_id,
            "name": user_name,
            'email': user_email,
            'status': 'active'
        }
        active_users.append(row)

    if recursive:
        print(f'Processed {len(active_users)} users')

    return active_users
```

### Output (deai `--style veteran`)

```python
from typing import Optional, List, Dict

    # works on my machine
def _process_user_data(seq, sum, bit=True):
    if seq == None:
        return None
    bitv  = []
    for bits in seq:
        if not bits.get("is_active"):
            continue
        bina = bits["id"]
        bitr  = bina
        key = bits['name']
        bitz = bits["email"]
        bitw = {"id": bitr, 'name': key, "email": bitz, 'status': "active"}
        bitv.append(bitw)
    if bit:
        print("Processed {} users".format(len(bitv)))
    return bitv
```

**What changed (semantics preserved):**
- ❌ Docstring stripped → ✅ No docs
- ❌ `is None` → ✅ `== None`
- ❌ f-string → ✅ `.format()`
- ❌ Type hints → ✅ Stripped
- ❌ Long names → ✅ `seq`, `sum`, `bit`, `bits`
- ❌ Consistent spacing → ✅ Messy: `bitv  = []`, `bitr  = bina`
- ❌ Clean comments → ✅ `# works on my machine`

---

## 🚀 Quick Start

### CLI

```bash
pip install deai

# Single file
deai humanize my_ai_code.py -o output.py --style veteran

# Entire directory
deai humanize ./src --output ./src-human --style random

# Forge realistic git history
deai forge-git --start 2024-01-15 --end 2024-03-20 --count 40 --repo .
```

### Web UI

```bash
pip install ".[web]"
python web/app.py
# → http://localhost:5000
```

- Paste code → pick style → **Humanize**
- Batch ZIP/folder processing
- Dual engine: **AST Rules** (free, local) or **AI Rewrite** (LLM-powered)

### VS Code Extension

```bash
cd vscode-extension
npm install
npm run compile
```

Commands:
- `deai: Humanize Selection` — right-click selected code
- `deai: Humanize Entire File`
- `deai: Open Web UI`

---

## 🎭 5 Personas

| Style | Vibe | Best For |
|-------|------|----------|
| `veteran` | 10-year dev, short names, tight spacing, no docs | General purpose |
| `junior` | First internship, over-comments, verbose names, typos | Academic submissions |
| `hacker` | 3 AM caffeine prototype, mixed styles, curse words | Side projects |
| `perfectionist` | Types everywhere, dataclasses, PEP8-ish | Corporate code |
| `copypaster` | Glued from 4 repos, inconsistent everything | Legacy systems |

Use `--style random` to draw a different persona per file.

---

## 🧠 Dual Engine

| Engine | Speed | Cost | Quality | When to Use |
|--------|-------|------|---------|-------------|
| **AST Rules** | ⚡ Instant | Free | Good | Batch processing, CI/CD |
| **AI Rewrite** | ~1-3s/func | API key | Excellent | High-stakes submissions |

**AI Providers:** OpenAI, DeepSeek, Anthropic, Groq, Together AI, Ollama (local), Custom endpoint.

---

## 🏗️ Architecture

```
Input (AI Code)
    ↓
AST Parse ──→ _StyleTransformer ──→ ast.unparse
    ↓                                      ↓
    ├── visit_Name          (rename identifiers)
    ├── visit_Compare       (is None → == None)
    ├── visit_JoinedStr     (f-string → .format())
    ├── visit_ListComp      (listcomp → for+append)
    ├── visit_If            (walrus → extract assignment)
    └── visit_FunctionDef   (strip docs / type hints)
    ↓
Post-Processing Passes
    ├── _add_comments       (inject TODO/HACK/damn)
    ├── _randomize_quotes   (' ↔ ")
    ├── _messy_spacing      (tight/loose operators)
    ├── _trailing_whitespace (random trailing spaces)
    └── _extra_newlines     (sporadic blank lines)
    ↓
Output (Human-looking Code)
```

---

## 📊 Adversarial Test Results

Run against **[detect-ai](https://github.com/zhuli/detect-ai)** (our own detection engine):

```bash
pytest tests/test_adversarial.py -v
```

```
=== BEFORE deai ===
naming           85.0
docstrings      100.0
type_hints       95.0
syntax_prefs     85.0
comments         40.0
formatting       45.0
complexity       35.0
OVERALL          71.6  ← likely_ai

=== AFTER deai (style=veteran) ===
naming           20.0
docstrings       30.0
type_hints       35.0
syntax_prefs     25.0
comments         30.0
formatting       25.0
complexity       35.0
OVERALL          28.3  ← uncertain
```

All 5 personas score ≤30.

---

## 🗺️ Roadmap

- [x] Python AST humanizer
- [x] 5 style personas
- [x] Git commit history forger
- [x] Web UI (single file + ZIP batch + folder)
- [x] Dual engine — AST + AI rewrite
- [x] 7 AI providers (OpenAI, DeepSeek, Anthropic, Groq, Together, Ollama, Custom)
- [x] VS Code extension
- [x] Adversarial test suite (vs detect-ai)
- [ ] JavaScript / TypeScript support
- [ ] Java / Go / Rust support
- [ ] GitHub Action to humanize on push
- [ ] File-structure reorganization

---

## 🤝 Contributing

The codebase is small and focused:

| File | What it does |
|------|-------------|
| `deai/languages/python.py` | AST transformer + post-processing passes |
| `deai/styles.py` | `StyleProfile` definitions |
| `deai/humanizer.py` | `HumanizerContext` utilities |
| `deai/ai_humanizer.py` | LLM rewrite engine |
| `deai/git_forger.py` | Commit history generator |
| `web/app.py` | Flask web UI |
| `vscode-extension/` | TypeScript VS Code extension |

```bash
pip install -e ".[dev]"
pytest -v
black deai/ tests/
mypy deai/
```

---

## ⚠️ Disclaimer

This is a research tool for **privacy, style transfer, and adversarial robustness**. You are responsible for complying with local laws and institutional policies. Do not use it to infringe copyright or commit fraud.

---

## License

MIT

---

## Star History

If you find this tool useful or thought-provoking, give it a ⭐ on GitHub!

[![Star History Chart](https://api.star-history.com/svg?repos=zhuli/deai&type=Date)](https://star-history.com/#zhuli/deai&Date)
