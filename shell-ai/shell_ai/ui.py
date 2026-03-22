"""Stylish terminal UI components for Shell AI."""
from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from rich.columns import Columns
from rich.table import Table
from rich import box

CUSTOM_THEME = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "accent": "bold #D4A574",
    "muted": "dim white",
    "success": "bold green",
    "provider.claude": "bold #D4A574",
    "provider.chatgpt": "bold #74AA9C",
    "provider.gemini": "bold #4285F4",
})

console = Console(theme=CUSTOM_THEME)


async def print_banner():
    """Play intro reveal animation, then start the continuous background animation."""
    from shell_ai.animations import animate_banner, banner_animator

    # Phase 1: intro reveal (letters appear, subtitle types in)
    await animate_banner(console)

    # Phase 2: set up scroll region and start continuous gradient loop
    banner_animator.start()


def stop_banner():
    """Stop the continuous banner animation and reset terminal."""
    from shell_ai.animations import banner_animator
    banner_animator.stop()


def build_welcome_table(provider_name: str, model: str, available: list[tuple[str, object]]) -> Table:
    table = Table(
        show_header=False,
        box=box.ROUNDED,
        border_style="#8B5CF6",
        padding=(0, 2),
        title="[bold #8B5CF6]Configuration[/]",
        title_style="bold",
    )
    table.add_column(style="dim white", width=16)
    table.add_column(style="bold white")

    table.add_row("Active Model", f"[bold]{provider_name}[/] / [cyan]{model}[/]")

    provider_tags = []
    for key, prov in available:
        color = prov.info.color
        icon = prov.info.icon
        provider_tags.append(f"[{color}]{icon} {prov.info.name}[/]")
    table.add_row("Providers", "  ".join(provider_tags))
    table.add_row("Help", "[dim]/help  /models  /switch  /clear  /exit[/]")

    return table


async def print_welcome(provider_name: str, model: str, available: list[tuple[str, object]]):
    from shell_ai.animations import animate_welcome_table
    table = build_welcome_table(provider_name, model, available)
    await animate_welcome_table(console, table)


def print_divider():
    console.rule(style="#3B3157")


def print_error(msg: str):
    console.print(f"[bold red]  Error:[/] {msg}")


def print_info(msg: str):
    console.print(f"[dim cyan]  {msg}[/]")


def print_success(msg: str):
    console.print(f"[bold green]  {msg}[/]")


def print_assistant_start(provider_name: str, color: str, icon: str):
    console.print(f"\n[{color}]{icon} {provider_name}[/]", end="")
    console.print(" [dim]─────────────────────────────────────[/]")


def print_assistant_end():
    console.print()


def render_markdown(text: str):
    md = Markdown(text, code_theme="monokai")
    console.print(md, end="")


def print_streaming_token(token: str):
    console.print(token, end="", highlight=False)


def print_models_table(providers: dict):
    table = Table(
        title="[bold #8B5CF6]Available Models[/]",
        box=box.ROUNDED,
        border_style="#8B5CF6",
        padding=(0, 2),
    )
    table.add_column("Provider", style="bold", width=12)
    table.add_column("Models", style="cyan")
    table.add_column("Status", width=12, justify="center")

    for key, prov in providers.items():
        status = "[green]Ready[/]" if prov.is_configured() else "[red]No Key[/]"
        color = prov.info.color
        models_str = "\n".join(prov.info.models)
        table.add_row(
            f"[{color}]{prov.info.icon} {prov.info.name}[/]",
            models_str,
            status,
        )

    console.print(table)


def print_help():
    table = Table(
        title="[bold #8B5CF6]Commands[/]",
        box=box.ROUNDED,
        border_style="#8B5CF6",
        padding=(0, 2),
        show_header=False,
    )
    table.add_column(style="bold cyan", width=24)
    table.add_column(style="white")

    commands = [
        ("/help", "Show this help message"),
        ("/setup", "Configure API keys (interactive wizard)"),
        ("/models", "List all available models"),
        ("/switch <provider>", "Switch AI provider (claude, chatgpt, gemini)"),
        ("/model <name>", "Switch to a specific model"),
        ("/clear", "Clear conversation history"),
        ("/system <prompt>", "Set system prompt"),
        ("/config", "Show current configuration"),
        ("/exit, /quit, Ctrl+D", "Exit Shell AI"),
        ("", ""),
        ("[dim]Ctrl+J / Shift+Enter[/]", "[dim]New line in input[/]"),
    ]
    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print(table)


def print_config(provider: str, model: str, system_prompt: str):
    table = Table(
        title="[bold #8B5CF6]Current Config[/]",
        box=box.ROUNDED,
        border_style="#8B5CF6",
        padding=(0, 2),
        show_header=False,
    )
    table.add_column(style="dim white", width=16)
    table.add_column(style="white")

    table.add_row("Provider", f"[bold]{provider}[/]")
    table.add_row("Model", f"[cyan]{model}[/]")
    table.add_row("System Prompt", system_prompt[:80] + ("..." if len(system_prompt) > 80 else ""))

    console.print(table)
