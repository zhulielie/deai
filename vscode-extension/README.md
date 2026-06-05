# deai — VS Code Extension

Transform AI-generated Python code to look hand-written, directly inside VS Code.

## Features

- **Humanize Selection** — Select any Python code, right-click → "Humanize Selection"
- **Humanize File** — Transform the entire current file
- **Dual Engine** — Choose between fast local AST rules or powerful AI rewrite
- **7 AI Providers** — OpenAI, DeepSeek, Anthropic, Groq, Together AI, Ollama (local), Custom
- **5 Personas** — Veteran, Junior, Hacker, Perfectionist, Copypaster

## Requirements

1. Install the Python package:
   ```bash
   pip install deai
   ```
2. For AI mode, configure your API key in VS Code settings.

## Usage

### Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| `deai: Humanize Selection` | — | Humanize selected code |
| `deai: Humanize Entire File` | — | Humanize the whole file |
| `deai: Open Web UI` | — | Open the web interface |

### Settings

Open VS Code settings (Ctrl+,) and search for "deai":

| Setting | Default | Description |
|---------|---------|-------------|
| `deai.engine` | `ast` | `ast` (local) or `ai` (LLM) |
| `deai.style` | `random` | Persona style |
| `deai.provider` | `openai` | AI provider (AI mode only) |
| `deai.apiKey` | ` ` | API key (AI mode only) |
| `deai.baseUrl` | ` ` | Custom base URL |
| `deai.model` | ` ` | Custom model name |

### Ollama (Local, Free)

1. Install [Ollama](https://ollama.com)
2. Pull a model: `ollama pull llama3.2`
3. Set `deai.provider` to `ollama`
4. Set `deai.engine` to `ai`
5. No API key needed!
