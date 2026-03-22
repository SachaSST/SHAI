<p align="center">
  <img src="https://img.shields.io/badge/python-≥3.11-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/version-0.1.0-purple?style=for-the-badge" />
</p>

<h1 align="center">
  ◈ SHAI — Shell AI
</h1>

<p align="center">
  <strong>A stylish, multi-model AI assistant that lives in your terminal.</strong><br/>
  Chat with <b>Claude</b>, <b>ChatGPT</b>, and <b>Gemini</b> — all from one place.<br/>
  Animated UI · Streaming responses · Switch models on the fly
</p>

<p align="center">
  <img width="680" alt="SHAI demo" src="https://github.com/user-attachments/assets/placeholder-demo.gif" />
</p>

---

## Features

- **3 AI providers in one tool** — Claude (Anthropic), ChatGPT (OpenAI), Gemini (Google) with streaming responses
- **Animated ASCII banner** — continuously flowing gradient that lives at the top of your terminal
- **Interactive setup wizard** — guided API key configuration with connection testing, masked key display, and secure storage (`chmod 600`)
- **Switch providers on the fly** — jump between Claude, ChatGPT, and Gemini mid-conversation
- **Rich terminal UI** — powered by [Rich](https://github.com/Textualize/rich) with colored panels, styled tables, spinners, and particle effects
- **Persistent history** — command history saved across sessions
- **TOML configuration** — customizable system prompts, default provider, and more
- **Slash commands** — `/switch`, `/model`, `/setup`, `/clear`, `/config`, and more

---

## Quick Start

### 1. Install

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/shell-ai.git
cd shell-ai

# Install (editable mode recommended)
pip install -e .
```

### 2. Launch

```bash
shai
```

On first launch, the **interactive setup wizard** will guide you through configuring your API keys:

```
╔═══════════════════════════╗
║  ⚙  API Key Setup        ║
╚═══════════════════════════╝

╭─────┬──────────────┬────────────────┬──────────────────╮
│  #  │ Provider     │     Status     │ API Key          │
├─────┼──────────────┼────────────────┼──────────────────┤
│  1  │ ◈ Claude     │  ✓ Connected   │ sk-ant••••••abc4 │
│  2  │ ◉ ChatGPT    │  ✗ Not set     │ ─                │
│  3  │ ◆ Gemini     │  ✗ Not set     │ ─                │
╰─────┴──────────────┴────────────────┴──────────────────╯
```

You only need **one** provider to get started.

### 3. Chat

```
 ❯ Explain how async generators work in Python
```

That's it. Responses stream in real-time with syntax highlighting.

---

## Supported Providers & Models

| Provider | Icon | Models | Env Variable |
|----------|------|--------|-------------|
| **Claude** (Anthropic) | ◈ | `claude-sonnet-4-20250514`, `claude-opus-4-20250514`, `claude-haiku-4-5-20251001` | `ANTHROPIC_API_KEY` |
| **ChatGPT** (OpenAI) | ◉ | `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `o3-mini` | `OPENAI_API_KEY` |
| **Gemini** (Google) | ◆ | `gemini-2.0-flash`, `gemini-2.5-pro-preview-05-06`, `gemini-2.0-flash-lite` | `GEMINI_API_KEY` |

API keys can be configured via the setup wizard (`/setup`) or environment variables.

---

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/setup` | Open the interactive API key wizard |
| `/switch <provider>` | Switch provider (`claude`, `chatgpt`, `gemini`) |
| `/model <name>` | Switch to a specific model |
| `/models` | List all available models and their status |
| `/clear` | Clear conversation history |
| `/system <prompt>` | View or set the system prompt |
| `/config` | Show current configuration |
| `/exit` or `Ctrl+D` | Exit SHAI |

**Keyboard shortcuts:**

| Shortcut | Action |
|----------|--------|
| `Ctrl+J` | Insert a new line (multi-line input) |
| `Ctrl+D` | Exit |
| `↑` / `↓` | Navigate command history |

---

## Configuration

SHAI stores its configuration in `~/.shell-ai/`:

```
~/.shell-ai/
├── config.toml    # Preferences (provider, model, system prompt)
├── keys.json      # API keys (chmod 600, git-ignored)
└── history        # Command history
```

### config.toml

```toml
provider = "claude"
model = ""
system_prompt = "You are a helpful AI coding assistant..."
max_history = 50
theme = "default"
```

### Environment variable overrides

```bash
export SHAI_PROVIDER=chatgpt   # Override default provider
export SHAI_MODEL=gpt-4o-mini  # Override default model
```

---

## Architecture

```
shell_ai/
├── __init__.py       # Package metadata
├── main.py           # Entry point, async event loop, command routing
├── providers.py      # AI provider abstraction (Claude, ChatGPT, Gemini)
├── ui.py             # Rich-based terminal UI components
├── animations.py     # Animated banner, spinners, gradient effects
├── config.py         # TOML config + secure key storage
└── setup.py          # Interactive API key setup wizard
```

**Tech stack:**
- [Rich](https://github.com/Textualize/rich) — styled terminal output, tables, panels, markdown rendering
- [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) — async input, history, key bindings
- [anthropic](https://github.com/anthropics/anthropic-sdk-python) — Claude API
- [openai](https://github.com/openai/openai-python) — ChatGPT API
- [google-genai](https://github.com/googleapis/python-genai) — Gemini API

---

## Requirements

- Python **≥ 3.11**
- A modern terminal with true color support (WezTerm, Alacritty, Ghostty, Kitty, iTerm2, Windows Terminal)
- At least one API key from a supported provider

---

## Security

- API keys are stored in `~/.shell-ai/keys.json` with **`600` permissions** (owner read/write only)
- Keys are **never** logged, committed, or displayed in plain text — they appear masked as `sk-ant••••••abc4`
- The `keys.json` file is included in `.gitignore` by default
- Environment variables take precedence over stored keys

---

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

```bash
# Development setup
git clone https://github.com/YOUR_USERNAME/shell-ai.git
cd shell-ai
pip install -e .
shai
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ◈ by humans and AI
</p>
