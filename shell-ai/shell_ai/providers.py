"""AI provider abstraction for Claude, ChatGPT, and Gemini."""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class Message:
    role: str  # "user", "assistant", "system"
    content: str


@dataclass
class ProviderInfo:
    name: str
    color: str
    icon: str
    models: list[str]


class BaseProvider(ABC):
    info: ProviderInfo

    @abstractmethod
    async def stream(self, messages: list[Message], model: str | None = None) -> AsyncIterator[str]:
        """Stream response tokens from the provider."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if API key is set."""
        ...

    def default_model(self) -> str:
        return self.info.models[0]


# ─── Claude ───────────────────────────────────────────────────────────────────

class ClaudeProvider(BaseProvider):
    info = ProviderInfo(
        name="Claude",
        color="#D4A574",
        icon="◈",
        models=["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-5-20251001"],
    )

    def is_configured(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    async def stream(self, messages: list[Message], model: str | None = None) -> AsyncIterator[str]:
        import anthropic

        client = anthropic.AsyncAnthropic()
        model = model or self.default_model()

        system_msg = None
        api_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                api_messages.append({"role": m.role, "content": m.content})

        kwargs: dict = dict(model=model, max_tokens=4096, messages=api_messages)
        if system_msg:
            kwargs["system"] = system_msg

        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text


# ─── ChatGPT ─────────────────────────────────────────────────────────────────

class ChatGPTProvider(BaseProvider):
    info = ProviderInfo(
        name="ChatGPT",
        color="#74AA9C",
        icon="◉",
        models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini"],
    )

    def is_configured(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

    async def stream(self, messages: list[Message], model: str | None = None) -> AsyncIterator[str]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI()
        model = model or self.default_model()

        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        stream = await client.chat.completions.create(
            model=model,
            messages=api_messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content


# ─── Gemini ───────────────────────────────────────────────────────────────────

class GeminiProvider(BaseProvider):
    info = ProviderInfo(
        name="Gemini",
        color="#4285F4",
        icon="◆",
        models=["gemini-2.0-flash", "gemini-2.5-pro-preview-05-06", "gemini-2.0-flash-lite"],
    )

    def is_configured(self) -> bool:
        return bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))

    async def stream(self, messages: list[Message], model: str | None = None) -> AsyncIterator[str]:
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        model = model or self.default_model()

        # Build content for Gemini
        system_instruction = None
        contents = []
        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m.content}]})

        config = {}
        if system_instruction:
            config["system_instruction"] = system_instruction

        async for chunk in client.aio.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text


# ─── Registry ─────────────────────────────────────────────────────────────────

PROVIDERS: dict[str, BaseProvider] = {
    "claude": ClaudeProvider(),
    "chatgpt": ChatGPTProvider(),
    "gemini": GeminiProvider(),
}


def get_provider(name: str) -> BaseProvider:
    key = name.lower().strip()
    if key in PROVIDERS:
        return PROVIDERS[key]
    raise ValueError(f"Unknown provider: {name}. Available: {', '.join(PROVIDERS)}")


def list_available_providers() -> list[tuple[str, BaseProvider]]:
    return [(k, v) for k, v in PROVIDERS.items() if v.is_configured()]
