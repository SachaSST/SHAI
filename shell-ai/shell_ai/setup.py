"""Interactive API key setup wizard for Shell AI."""
from __future__ import annotations

import os
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich import box

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style as PTStyle

from shell_ai.config import Config, CONFIG_DIR, KEYS_FILE, load_keys, save_keys

SETUP_STYLE = PTStyle.from_dict({
    "": "#E0E0E0",
    "prompt": "#8B5CF6 bold",
})

_session = PromptSession(style=SETUP_STYLE)

PROVIDERS_META = [
    {
        "key": "claude",
        "name": "Claude",
        "icon": "◈",
        "color": "#D4A574",
        "env_var": "ANTHROPIC_API_KEY",
        "url": "https://console.anthropic.com/settings/keys",
        "prefix": "sk-ant-",
        "description": "Anthropic's Claude models",
    },
    {
        "key": "chatgpt",
        "name": "ChatGPT",
        "icon": "◉",
        "color": "#74AA9C",
        "env_var": "OPENAI_API_KEY",
        "url": "https://platform.openai.com/api-keys",
        "prefix": "sk-",
        "description": "OpenAI's GPT models",
    },
    {
        "key": "gemini",
        "name": "Gemini",
        "icon": "◆",
        "color": "#4285F4",
        "env_var": "GEMINI_API_KEY",
        "url": "https://aistudio.google.com/apikey",
        "prefix": "",
        "description": "Google's Gemini models",
    },
]


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "•" * len(key)
    return key[:6] + "••••••" + key[-4:]


def _get_status_icon(configured: bool) -> str:
    return "✓" if configured else "✗"


def print_setup_header(console: Console):
    header = Text()
    header.append("  ⚙  ", style="bold #8B5CF6")
    header.append("API Key Setup", style="bold white")

    console.print()
    console.print(Panel(
        header,
        border_style="#8B5CF6",
        box=box.DOUBLE_EDGE,
        padding=(0, 2),
    ))
    console.print()


def print_keys_status(console: Console, keys: dict[str, str]):
    table = Table(
        box=box.ROUNDED,
        border_style="#3B3157",
        padding=(0, 1),
        show_header=True,
        header_style="bold #A78BFA",
        title="[bold #8B5CF6]  Provider Status[/]",
        title_style="bold",
    )
    table.add_column("#", style="dim", width=3, justify="center")
    table.add_column("Provider", width=12)
    table.add_column("Status", width=14, justify="center")
    table.add_column("API Key")

    for i, meta in enumerate(PROVIDERS_META, 1):
        stored_key = keys.get(meta["env_var"], "")
        env_key = os.environ.get(meta["env_var"], "")
        active_key = stored_key or env_key
        is_configured = bool(active_key)

        color = meta["color"]
        icon = meta["icon"]
        name_styled = f"[{color}]{icon} {meta['name']}[/]"

        if is_configured:
            status = "[bold green]✓ Connected[/]"
            key_display = f"[dim]{_mask_key(active_key)}[/]"
            if env_key and not stored_key:
                key_display += " [dim yellow](env)[/]"
        else:
            status = "[dim red]✗ Not set[/]"
            key_display = "[dim]─[/]"

        table.add_row(f"[bold]{i}[/]", name_styled, status, key_display)

    console.print(table)
    console.print()


def print_setup_menu(console: Console):
    menu = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 1),
        show_edge=False,
    )
    menu.add_column(style="bold #8B5CF6", width=6, justify="center")
    menu.add_column(style="white")

    menu.add_row("[bold cyan]1-3[/]", "Configure a provider's API key")
    menu.add_row("[bold cyan]r[/]", "Remove a provider's API key")
    menu.add_row("[bold cyan]t[/]", "Test all configured connections")
    menu.add_row("[bold cyan]q[/]", "Done — return to chat")

    console.print(Panel(
        menu,
        title="[bold #8B5CF6]  Actions[/]",
        border_style="#3B3157",
        box=box.ROUNDED,
        padding=(0, 1),
    ))


async def _prompt_input(label: str, password: bool = False) -> str:
    styled = HTML(f'<style fg="#8B5CF6" bold="true">  {label} </style><style fg="#A78BFA">▸ </style>')
    try:
        return (await _session.prompt_async(styled, is_password=password)).strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def _animate_status(console: Console, message: str, success: bool):
    if success:
        console.print(f"  [bold green]✓[/] {message}")
    else:
        console.print(f"  [bold red]✗[/] {message}")


async def _test_provider(key: str, env_var: str, provider_key: str) -> tuple[bool, str]:
    """Test a provider connection with the given key."""
    old_val = os.environ.get(env_var)
    os.environ[env_var] = key
    try:
        if provider_key == "claude":
            import anthropic
            client = anthropic.AsyncAnthropic()
            msg = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return True, "Connection successful"
        elif provider_key == "chatgpt":
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return True, "Connection successful"
        elif provider_key == "gemini":
            from google import genai
            client = genai.Client(api_key=key)
            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents="Hi",
            )
            return True, "Connection successful"
    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 80:
            error_msg = error_msg[:80] + "..."
        return False, error_msg
    finally:
        if old_val is not None:
            os.environ[env_var] = old_val
        elif env_var in os.environ:
            del os.environ[env_var]


async def configure_provider(console: Console, keys: dict[str, str], index: int):
    if index < 0 or index >= len(PROVIDERS_META):
        return

    meta = PROVIDERS_META[index]
    color = meta["color"]
    name = meta["name"]
    icon = meta["icon"]

    console.print()
    console.print(Panel(
        f"[{color}]{icon} {name}[/]  ─  {meta['description']}",
        border_style=color,
        box=box.ROUNDED,
        padding=(0, 2),
    ))
    console.print(f"  [dim]Get your key at:[/] [bold cyan]{meta['url']}[/]")
    console.print()

    key = await _prompt_input(f"{name} API Key (hidden):", password=True)
    if not key:
        console.print("  [dim]Cancelled.[/]")
        return

    # Validate prefix
    if meta["prefix"] and not key.startswith(meta["prefix"]):
        console.print(f"  [yellow]⚠ Key doesn't start with '{meta['prefix']}' — might be invalid[/]")
        confirm = await _prompt_input("Save anyway? (y/n):")
        if confirm.lower() != "y":
            console.print("  [dim]Cancelled.[/]")
            return

    keys[meta["env_var"]] = key
    save_keys(keys)

    # Also export to current process
    os.environ[meta["env_var"]] = key

    console.print()
    _animate_status(console, f"{name} API key saved and activated", True)
    console.print()


async def remove_provider(console: Console, keys: dict[str, str]):
    console.print()
    choice = await _prompt_input("Provider number to remove (1-3):")
    if not choice.isdigit():
        return

    index = int(choice) - 1
    if index < 0 or index >= len(PROVIDERS_META):
        console.print("  [dim]Invalid selection.[/]")
        return

    meta = PROVIDERS_META[index]
    env_var = meta["env_var"]

    if env_var in keys:
        del keys[env_var]
        save_keys(keys)

    if env_var in os.environ:
        del os.environ[env_var]

    _animate_status(console, f"{meta['name']} API key removed", True)
    console.print()


async def test_connections(console: Console, keys: dict[str, str]):
    console.print()
    console.print("  [bold #8B5CF6]Testing connections...[/]")
    console.print()

    for meta in PROVIDERS_META:
        env_var = meta["env_var"]
        active_key = keys.get(env_var) or os.environ.get(env_var, "")
        color = meta["color"]
        name = meta["name"]
        icon = meta["icon"]

        if not active_key:
            console.print(f"  [{color}]{icon} {name:<10}[/]  [dim]— skipped (no key)[/]")
            continue

        console.print(f"  [{color}]{icon} {name:<10}[/]  [dim]testing...[/]", end="")

        success, message = await _test_provider(active_key, env_var, meta["key"])

        # Clear the line and rewrite
        console.print(f"\r  [{color}]{icon} {name:<10}[/]  ", end="")
        if success:
            console.print(f"[bold green]✓ {message}[/]")
        else:
            console.print(f"[bold red]✗ {message}[/]")

    console.print()


async def run_setup(console: Console) -> str | None:
    """Run the interactive setup wizard. Returns the provider key to use, or None."""
    keys = load_keys()

    # Load saved keys into environment for the current session
    for meta in PROVIDERS_META:
        env_var = meta["env_var"]
        if env_var in keys and env_var not in os.environ:
            os.environ[env_var] = keys[env_var]

    print_setup_header(console)

    first_configured = None

    while True:
        print_keys_status(console, keys)
        print_setup_menu(console)
        console.print()

        choice = await _prompt_input("Choice:")
        choice = choice.lower().strip()

        if choice in ("q", "quit", "done", ""):
            # Find first configured provider to return
            for meta in PROVIDERS_META:
                if keys.get(meta["env_var"]) or os.environ.get(meta["env_var"]):
                    first_configured = meta["key"]
                    break
            break
        elif choice in ("1", "2", "3"):
            await configure_provider(console, keys, int(choice) - 1)
        elif choice == "r":
            await remove_provider(console, keys)
        elif choice == "t":
            await test_connections(console, keys)
        else:
            console.print("  [dim]Invalid choice. Use 1-3, r, t, or q.[/]")

        console.print()

    return first_configured


def needs_setup() -> bool:
    """Check if at least one provider is configured (env or stored keys)."""
    keys = load_keys()
    for meta in PROVIDERS_META:
        env_var = meta["env_var"]
        if keys.get(env_var) or os.environ.get(env_var):
            return False
    return True


def load_keys_into_env():
    """Load stored API keys into environment variables."""
    keys = load_keys()
    for meta in PROVIDERS_META:
        env_var = meta["env_var"]
        if env_var in keys and env_var not in os.environ:
            os.environ[env_var] = keys[env_var]
