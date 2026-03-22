"""Main entry point for Shell AI."""
from __future__ import annotations

import asyncio
import signal
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style as PTStyle

from shell_ai.config import Config, CONFIG_DIR, HISTORY_FILE
from shell_ai.providers import PROVIDERS, get_provider, Message
from shell_ai import ui


# ─── Prompt Toolkit Setup ────────────────────────────────────────────────────

PT_STYLE = PTStyle.from_dict({
    "prompt": "#8B5CF6 bold",
    "": "#E0E0E0",
})


def create_key_bindings() -> KeyBindings:
    kb = KeyBindings()

    @kb.add(Keys.ControlJ)
    def _(event):
        event.current_buffer.insert_text("\n")

    return kb


def get_prompt_text(provider_name: str, color: str) -> HTML:
    return HTML(f'<style fg="{color}" bold="true"> ❯ </style>')


# ─── Command Handler ─────────────────────────────────────────────────────────

class CommandResult:
    def __init__(self, handled: bool = True, exit: bool = False, run_setup: bool = False):
        self.handled = handled
        self.exit = exit
        self.run_setup = run_setup


async def handle_command(text: str, config: Config, conversation: list[Message]) -> CommandResult:
    parts = text.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ("/exit", "/quit"):
        return CommandResult(exit=True)

    elif cmd == "/help":
        ui.print_help()

    elif cmd == "/setup":
        return CommandResult(run_setup=True)

    elif cmd == "/models":
        ui.print_models_table(PROVIDERS)

    elif cmd == "/switch":
        if not arg:
            ui.print_error("Usage: /switch <provider>  (claude, chatgpt, gemini)")
            return CommandResult()
        try:
            prov = get_provider(arg)
            if not prov.is_configured():
                ui.print_error(f"{prov.info.name} is not configured. Run /setup to add the API key.")
                return CommandResult()
            config.provider = arg.lower()
            config.model = None
            config.save()
            from shell_ai.animations import animate_switch
            await animate_switch(ui.console, prov.info.name, prov.info.color, prov.info.icon)
        except ValueError as e:
            ui.print_error(str(e))

    elif cmd == "/model":
        if not arg:
            ui.print_error("Usage: /model <model-name>")
            return CommandResult()
        config.model = arg.strip()
        config.save()
        ui.print_success(f"Model set to {config.model}")

    elif cmd == "/clear":
        conversation.clear()
        ui.print_success("Conversation cleared.")

    elif cmd == "/system":
        if not arg:
            ui.print_info(f"Current: {config.system_prompt}")
        else:
            config.system_prompt = arg
            config.save()
            ui.print_success("System prompt updated.")

    elif cmd == "/config":
        provider = get_provider(config.provider)
        model = config.model or provider.default_model()
        ui.print_config(provider.info.name, model, config.system_prompt)

    else:
        return CommandResult(handled=False)

    return CommandResult()


# ─── Shutdown ─────────────────────────────────────────────────────────────────

async def _shutdown(reason: str = "Shutting down..."):
    from shell_ai.animations import animate_loading
    ui.stop_banner()
    ui.console.print()
    await animate_loading(ui.console, reason, duration=0.5)
    ui.console.print("  [dim #A78BFA]Goodbye! [bold]✦[/][/]")


# ─── Main Loop ───────────────────────────────────────────────────────────────

async def chat_loop():
    from shell_ai.setup import needs_setup, run_setup, load_keys_into_env
    from shell_ai.animations import banner_animator

    config = Config.load()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Handle terminal resize to update scroll region
    def _on_resize(signum, frame):
        banner_animator.handle_resize()

    try:
        signal.signal(signal.SIGWINCH, _on_resize)
    except (AttributeError, OSError):
        pass  # SIGWINCH not available on this platform

    # Play intro + start continuous banner animation
    await ui.print_banner()

    # Load any saved API keys into env
    load_keys_into_env()

    # Auto-launch setup wizard if no provider is configured
    if needs_setup():
        ui.console.print("  [bold #A78BFA]No API keys configured yet. Let's set things up![/]")
        ui.console.print()
        provider_key = await run_setup(ui.console)
        if provider_key:
            config.provider = provider_key
            config.save()
        else:
            await _shutdown("No provider configured")
            return

    # Validate provider
    try:
        provider = get_provider(config.provider)
    except ValueError:
        config.provider = "claude"
        provider = get_provider(config.provider)

    if not provider.is_configured():
        from shell_ai.providers import list_available_providers
        available = list_available_providers()
        if available:
            config.provider = available[0][0]
            provider = available[0][1]
        else:
            ui.print_error("No AI provider is configured! Run /setup to add API keys.")
            ui.stop_banner()
            return

    model = config.model or provider.default_model()
    available = [(k, v) for k, v in PROVIDERS.items()]
    await ui.print_welcome(provider.info.name, model, available)

    # Prompt session
    session: PromptSession = PromptSession(
        history=FileHistory(str(HISTORY_FILE)),
        key_bindings=create_key_bindings(),
        style=PT_STYLE,
        multiline=False,
    )

    conversation: list[Message] = []

    while True:
        provider = get_provider(config.provider)
        model = config.model or provider.default_model()
        prompt_html = get_prompt_text(provider.info.name, provider.info.color)

        try:
            user_input = await session.prompt_async(prompt_html)
        except (EOFError, KeyboardInterrupt):
            await _shutdown()
            break

        text = user_input.strip()
        if not text:
            continue

        # Handle commands
        if text.startswith("/"):
            result = await handle_command(text, config, conversation)
            if result.exit:
                await _shutdown()
                break
            if result.run_setup:
                provider_key = await run_setup(ui.console)
                if provider_key:
                    config.provider = provider_key
                    config.save()
                    provider = get_provider(config.provider)
                    model = config.model or provider.default_model()
                    ui.print_success(f"Active provider: {provider.info.name} ({model})")
                continue
            if result.handled:
                continue

        # Add user message
        conversation.append(Message(role="user", content=text))

        # Build messages with system prompt
        messages = [Message(role="system", content=config.system_prompt)] + conversation[
            -(config.max_history * 2):
        ]

        # Stream response
        ui.print_assistant_start(provider.info.name, provider.info.color, provider.info.icon)

        full_response = ""
        try:
            async for token in provider.stream(messages, model):
                full_response += token
                ui.print_streaming_token(token)
        except Exception as e:
            ui.print_error(f"API error: {e}")
            conversation.pop()  # Remove failed user message
            continue

        ui.print_assistant_end()

        # Add assistant response to history
        conversation.append(Message(role="assistant", content=full_response))


def main():
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        # Ensure we reset the terminal even on hard interrupt
        from shell_ai.animations import banner_animator
        banner_animator.stop()


if __name__ == "__main__":
    main()
