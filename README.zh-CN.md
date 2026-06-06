<div align="center">

# ⚔️ deai — AI 代码Humanizer

**把 AI 写的代码变成看起来像人写的。**

*绕过 AI 检测、风格指纹识别和版权扫描器。*

[🇺🇸 English](README.md)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-22%2F22-brightgreen.svg)](https://github.com/zhulielie/deai/actions)
[![VS Code](https://img.shields.io/badge/VS%20Code-Extension-blueviolet.svg)](./vscode-extension)
[![Web UI](https://img.shields.io/badge/Web-UI-orange.svg)](./web)
[![在线体验](https://img.shields.io/badge/在线体验-00C7B7.svg)](https://deai-hv9k.onrender.com/)

</div>

---

## 🎯 一行命令，零 AI 指纹

现代 AI 编程助手会留下**可检测的指纹**：

| AI 指纹 | 人类代码 |
|---------|---------|
| 每个函数都有完美的 docstring | 缺失或只有一行注释 |
| 到处用 `is None` | 混用 `== None` |
| 100% f-string | 还有 `.format()` 和 `%` |
| 列表推导式 | 显式 `for` + `append` 循环 |
| 间距完美一致 | 运算符空格随机松紧 |
| 描述性命名（`processed_user_data_list`） | `tmp`、`buf`、`i`、`seq` |

**deai** 剥离这些指纹 —— 不是通过混淆逻辑，而是通过 AST 变换 + LLM 重写来改写*表面风格*。

---

## 🛡️ 实证：在 7 条规则上击败 detect-ai

我们构建了 **[detect-ai](https://github.com/zhulielie/detect-ai/blob/main/README.zh-CN.md)**（宿敌）来测试 deai。数据如下：

| detect-ai 规则 | AI 代码分数 | deai 伪装后 | Δ |
|----------------|-------------|-------------|---|
| **naming** | 85.0 | **20.0** | -77% |
| **docstrings** | 100.0 | **30.0** | -70% |
| **type_hints** | 95.0 | **35.0** | -63% |
| **syntax_preferences** | 85.0 | **25.0** | -71% |
| **comments** | 40.0 | **15~30** | -25~63% |
| **formatting** | 45.0 | **25~40** | -11~44% |
| **complexity** | 35.0 | **35.0** | — |
| **总分** | **71.6** | **26~30** | **-58%** |

所有 5 种人格都能以 **≤30** 的分数通过扫描器（`uncertain` / `likely_human` 区间）。

---

## 📸 Before vs After

### 输入（典型 AI 输出）

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

### 输出（deai `--style veteran`）

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

**变化（语义保留）：**
- ❌ Docstring 剥离 → ✅ 无文档
- ❌ `is None` → ✅ `== None`
- ❌ f-string → ✅ `.format()`
- ❌ 类型注解 → ✅ 剥离
- ❌ 长命名 → ✅ `seq`, `sum`, `bit`, `bits`
- ❌ 一致间距 → ✅ 混乱：`bitv  = []`, `bitr  = bina`
- ❌ 干净注释 → ✅ `# works on my machine`

---

## 🚀 快速开始

### CLI

```bash
pip install deai

# 单文件
deai humanize my_ai_code.py -o output.py --style veteran

# 整个目录
deai humanize ./src --output ./src-human --style random

# 伪造真实 git 历史
deai forge-git --start 2024-01-15 --end 2024-03-20 --count 40 --repo .
```

### Web UI

**在线体验**: https://deai-hv9k.onrender.com/

```bash
pip install ".[web]"
python web/app.py
# → http://localhost:5000
```

- 粘贴代码 → 选择风格 → **Humanize**
- 批量 ZIP/文件夹处理
- 双引擎：**AST 规则**（免费，本地）或 **AI 重写**（LLM 驱动）

### VS Code 扩展

```bash
cd vscode-extension
npm install
npm run compile
```

命令：
- `deai: Humanize Selection` — 右键选中代码
- `deai: Humanize Entire File`
- `deai: Open Web UI`

---

## 🎭 5 种人格

| 风格 | 氛围 | 最适合 |
|------|------|--------|
| `veteran` | 10 年老开发，短命名，紧凑间距，无文档 | 通用 |
| `junior` | 第一次实习，过度注释，冗长命名，拼写错误 | 学术提交 |
| `hacker` | 凌晨 3 点咖啡因原型，混合风格，脏话 |  side project |
| `perfectionist` | 到处都是类型，dataclass，PEP8 风格 | 企业代码 |
| `copypaster` | 从 4 个仓库粘的，一切都不一致 | 遗留系统 |

用 `--style random` 为每个文件随机抽取一种人格。

---

## 🧠 双引擎

| 引擎 | 速度 | 成本 | 质量 | 何时使用 |
|------|------|------|------|----------|
| **AST 规则** | ⚡ 即时 | 免费 | 良好 | 批量处理，CI/CD |
| **AI 重写** | ~1-3s/函数 | API key | 优秀 | 高风险提交 |

**AI 提供商：** OpenAI、DeepSeek、Anthropic、Groq、Together AI、Ollama（本地）、Custom endpoint。

---

## 🏗️ 架构

```
输入（AI 代码）
    ↓
AST 解析 ──→ _StyleTransformer ──→ ast.unparse
    ↓                                      ↓
    ├── visit_Name          （重命名标识符）
    ├── visit_Compare       （is None → == None）
    ├── visit_JoinedStr     （f-string → .format()）
    ├── visit_ListComp      （listcomp → for+append）
    ├── visit_If            （walrus → 提取赋值）
    └── visit_FunctionDef   （剥离文档 / 类型注解）
    ↓
后处理通道
    ├── _add_comments       （注入 TODO/HACK/脏话）
    ├── _randomize_quotes   （' ↔ "）
    ├── _messy_spacing      （松紧运算符空格）
    ├── _trailing_whitespace （随机尾部空格）
    └── _extra_newlines     （偶发空行）
    ↓
输出（看起来像人的代码）
```

---

## 📊 对抗测试结果

针对 **[detect-ai](https://github.com/zhulielie/detect-ai/blob/main/README.zh-CN.md)**（我们自己的检测引擎）运行：

```bash
pytest tests/test_adversarial.py -v
```

```
=== deai 之前 ===
naming           85.0
docstrings      100.0
type_hints       95.0
syntax_prefs     85.0
comments         40.0
formatting       45.0
complexity       35.0
总分             71.6  ← likely_ai

=== deai 之后（style=veteran）===
naming           20.0
docstrings       30.0
type_hints       35.0
syntax_prefs     25.0
comments         30.0
formatting       25.0
complexity       35.0
总分             28.3  ← uncertain
```

所有 5 种人格分数 ≤30。

---

## 🗺️ 路线图

- [x] Python AST humanizer
- [x] 5 种风格人格
- [x] Git commit history forger
- [x] Web UI（单文件 + ZIP 批量 + 文件夹）
- [x] 双引擎 — AST + AI 重写
- [x] 7 个 AI 提供商（OpenAI, DeepSeek, Anthropic, Groq, Together, Ollama, Custom）
- [x] VS Code 扩展
- [x] 对抗测试套件（vs detect-ai）
- [ ] JavaScript / TypeScript 支持
- [ ] Java / Go / Rust 支持
- [ ] GitHub Action push 时自动 humanize
- [ ] 文件结构重组

---

## 🤝 贡献

代码库小而聚焦：

| 文件 | 作用 |
|------|------|
| `deai/languages/python.py` | AST transformer + 后处理通道 |
| `deai/styles.py` | `StyleProfile` 定义 |
| `deai/humanizer.py` | `HumanizerContext` 工具 |
| `deai/ai_humanizer.py` | LLM 重写引擎 |
| `deai/git_forger.py` | Commit history 生成器 |
| `web/app.py` | Flask web UI |
| `vscode-extension/` | TypeScript VS Code 扩展 |

```bash
pip install -e ".[dev]"
pytest -v
black deai/ tests/
mypy deai/
```

---

## ⚠️ 免责声明

这是一个用于**隐私、风格转换和对抗鲁棒性**的研究工具。你有责任遵守当地法律和机构政策。请勿将其用于侵犯版权或欺诈。

---

## License

MIT

---

## Star History

如果觉得这个工具有用或引人深思，请在 GitHub 上给它一颗 ⭐！

[![Star History Chart](https://api.star-history.com/svg?repos=zhuli/deai&type=Date)](https://star-history.com/#zhuli/deai&Date)
