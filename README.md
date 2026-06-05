# deai — Make AI-Generated Code Look Human

> **Style anonymizer for AI-generated code.**  
> Built to pass software copyright AI detection, school code similarity checks, and corporate AI scanners.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/yourname/deai/actions)

---

## Why?

AI coding assistants write code that is **too clean**:

- Perfect docstrings on every function
- Consistent naming conventions across the whole repo
- Identical spacing and bracket style
- `is None` instead of `== None`
- Over-engineered error handling

All of these are **fingerprints**. Modern code scanners (including software copyright offices and university plagiarism systems) are training classifiers on exactly these patterns.

**deai** doesn't change what your code does. It changes *who it looks like it was written by*.

---

## Before vs After

### Input (Typical AI Output)

```python
def process_user_data(user_list: List[Dict], output_directory: str, verbose: bool = True) -> Optional[str]:
    """
    Process a list of user dictionaries and write the result to a JSON file.
    """
    if user_list is None:
        return None

    processed_results = []
    for user in user_list:
        if not user.get("is_active"):
            continue
        user_id = user["id"]
        user_name = user["name"]
        user_email = user["email"]
        processed_item = {"id": user_id, "name": user_name, "email": user_email, "status": "active"}
        processed_results.append(processed_item)
    # ...
```

### Output (deai with `--style random`)

```python
def _process_user_data(arr: List[Dict], result: str, entity: bool= True) ->  Optional[str]:
    # this is ugly, fix later
    if arr == None:
        return None
    val = []
    for row in arr:
        if not row.get("is_active"):
            continue
        tmp50 = row["id"]
        row1 = tmp50
        word = row['name']
        thing = row["email"]
        o =  {"id": row1, "name": word, "email": thing, 'status': 'active'}
        val.append(o)
    # ...
```

Notice:
- Function renamed with leading underscore
- Human-style typo comments injected
- `is None` → `== None`
- Temp variables added for no reason
- Mixed `'` and `"` quotes
- Random operator spacing
- Different naming style per scope

---

## Install

```bash
pip install deai
```

Or from source:

```bash
git clone https://github.com/yourname/deai.git
cd deai
pip install -e ".[dev]"
```

---

## Usage

### 1. Humanize a single file

```bash
deai humanize my_ai_code.py -o output.py
```

### 2. Humanize an entire directory

```bash
deai humanize ./src --output ./src-human --style random
```

### 3. Simulate a specific developer persona

```bash
deai humanize app.py -o app_dirty.py --style hacker
```

Available personas:

| Style | Vibe |
|-------|------|
| `veteran` | 10-year dev, short names, tight spacing, no docs |
| `junior` | First internship, over-comments, verbose names, typos |
| `hacker` | 3 AM caffeine prototype, mixed styles, curse words |
| `perfectionist` | Types everywhere, dataclasses, PEP8-ish |
| `copypaster` | Glued from 4 repos, inconsistent everything |

### 4. Forge realistic git history

Many copyright offices ask for **development process materials**. AI-generated repos usually have 1 commit: "Initial commit".

```bash
deai forge-git --start 2024-01-15 --end 2024-03-20 --count 40 --repo .
```

This generates `forge_commits.sh`. Run it in your repo to create a realistic backdated commit history with feature commits, bug fixes, WIPs, and weekend work patterns.

---

## How It Works

1. **AST-aware renaming** — we parse Python into an AST and rename variables/functions based on *human heuristics*, not random noise. Loop indices become `i`, `idx`, `ii`. Temporaries become `tmp`, `buf`, `t42`.
2. **Style fingerprint injection** — each persona has preferences for spacing, naming, type hints, docstrings, and comment density.
3. **Semantic micro-degradations** — convert `is None` to `== None`, insert `== True`, split assignments with meaningless temp variables.
4. **Git history simulation** — realistic timestamps, weekdays vs weekends, late-night commits, bugfix/feature/WIP ratios.

---

## Roadmap

- [x] Python AST humanizer
- [x] Style persona system
- [x] Git commit history forger
- [ ] JavaScript / TypeScript support
- [ ] Java / Go / Rust support
- [ ] File-structure reorganization (shuffle modules to look less engineered)
- [ ] README / doc humanizer
- [ ] GitHub Action to humanize on push

---

## Contributing

PRs are welcome! The codebase is small and focused:

- `deai/languages/python.py` — AST transformer + post-processing passes
- `deai/styles.py` — `StyleProfile` definitions
- `deai/humanizer.py` — `HumanizerContext` utilities
- `deai/git_forger.py` — commit history generator

Run tests:

```bash
pytest -v
```

Lint and type-check:

```bash
black deai/ tests/
mypy deai/
```

---

## Disclaimer

This is a research tool for **privacy, style transfer, and adversarial robustness**. You are responsible for complying with local laws and institutional policies. Do not use it to infringe copyright or commit fraud.

---

## License

MIT

---

## Star History

If you find this tool useful or thought-provoking, please consider giving it a ⭐ on GitHub!

[![Star History Chart](https://api.star-history.com/svg?repos=yourname/deai&type=Date)](https://star-history.com/#yourname/deai&Date)
