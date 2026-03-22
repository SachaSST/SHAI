"""Configuration management for Shell AI."""
from __future__ import annotations

import os
import json
import stat
from dataclasses import dataclass
from pathlib import Path

try:
    import toml
except ImportError:
    toml = None


CONFIG_DIR = Path.home() / ".shell-ai"
CONFIG_FILE = CONFIG_DIR / "config.toml"
KEYS_FILE = CONFIG_DIR / "keys.json"
HISTORY_FILE = CONFIG_DIR / "history"


# ─── API Keys Storage ────────────────────────────────────────────────────────

def load_keys() -> dict[str, str]:
    """Load stored API keys from keys.json."""
    if KEYS_FILE.exists():
        try:
            return json.loads(KEYS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_keys(keys: dict[str, str]):
    """Save API keys to keys.json with restrictive permissions (600)."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    KEYS_FILE.write_text(json.dumps(keys, indent=2))
    KEYS_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600 - owner read/write only


# ─── Config ──────────────────────────────────────────────────────────────────

@dataclass
class Config:
    provider: str = "claude"
    model: str | None = None
    system_prompt: str = "You are a helpful AI coding assistant running inside a terminal. Be concise, use markdown formatting. When showing code, always specify the language for syntax highlighting."
    max_history: int = 50
    theme: str = "default"

    @classmethod
    def load(cls) -> "Config":
        config = cls()
        if CONFIG_FILE.exists() and toml:
            data = toml.loads(CONFIG_FILE.read_text())
            for k, v in data.items():
                if hasattr(config, k):
                    setattr(config, k, v)
        # Env overrides
        if env_provider := os.environ.get("SHAI_PROVIDER"):
            config.provider = env_provider
        if env_model := os.environ.get("SHAI_MODEL"):
            config.model = env_model
        return config

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if toml:
            CONFIG_FILE.write_text(toml.dumps({
                "provider": self.provider,
                "model": self.model or "",
                "system_prompt": self.system_prompt,
                "max_history": self.max_history,
                "theme": self.theme,
            }))
