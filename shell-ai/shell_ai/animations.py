"""Terminal animations for Shell AI."""
from __future__ import annotations

import asyncio
import math
import os
import random
import shutil
import sys
import time

from rich.console import Console
from rich.live import Live
from rich.text import Text


# ─── Color Utilities ──────────────────────────────────────────────────────────

def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def _lerp_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return _rgb_to_hex(r, g, b)


# Gradient palette: purple -> blue -> cyan -> purple
GRADIENT = ["#6D28D9", "#7C3AED", "#8B5CF6", "#A78BFA", "#818CF8", "#6366F1", "#4F46E5", "#4338CA"]


def _wave_color(col: int, frame: int, total_cols: int) -> str:
    """Get a color from the gradient that shifts over time."""
    idx = (col / max(total_cols, 1) * len(GRADIENT) + frame * 0.3) % len(GRADIENT)
    i = int(idx) % len(GRADIENT)
    j = (i + 1) % len(GRADIENT)
    t = idx - int(idx)
    return _lerp_color(GRADIENT[i], GRADIENT[j], t)


# ─── Banner Data ──────────────────────────────────────────────────────────────

BANNER_LINES = [
    "  ███████╗██╗  ██╗ █████╗ ██╗",
    "  ██╔════╝██║  ██║██╔══██╗██║",
    "  ███████╗███████║███████║██║",
    "  ╚════██║██╔══██║██╔══██║██║",
    "  ███████║██║  ██║██║  ██║██║",
    "  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝",
]

SUBTITLE = "── Multi-Model AI Shell Assistant ──"

PARTICLES = ["✦", "✧", "·", "•", "∘", "◦", "⊹", "⋆"]

# Banner height: 1 empty + 6 logo + 1 subtitle + 1 empty = 9 lines
BANNER_HEIGHT = 9


# ─── Animated Banner (intro reveal) ──────────────────────────────────────────

def _render_banner_frame(frame: int, total_frames: int) -> Text:
    """Render one frame of the intro reveal animation."""
    output = Text()
    output.append("\n")

    max_cols = max(len(line) for line in BANNER_LINES)

    for row, line in enumerate(BANNER_LINES):
        reveal_progress = min(1.0, (frame - row * 0.8) / 4.0)

        if reveal_progress <= 0:
            output.append(" " * len(line) + "\n")
            continue

        chars_to_show = int(len(line) * min(1.0, reveal_progress))

        for col, ch in enumerate(line):
            if col < chars_to_show:
                color = _wave_color(col, frame - row, max_cols)
                output.append(ch, style=f"bold {color}")
            else:
                output.append(" ")

        output.append("\n")

    # Subtitle with typing effect
    subtitle_start_frame = 8
    if frame >= subtitle_start_frame:
        sub_progress = min(1.0, (frame - subtitle_start_frame) / 8.0)
        chars = int(len(SUBTITLE) * sub_progress)
        output.append("  ")
        for i, ch in enumerate(SUBTITLE[:chars]):
            t = i / max(len(SUBTITLE), 1)
            color = _lerp_color("#A78BFA", "#6D28D9", t)
            output.append(ch, style=f"dim {color}")
        if sub_progress < 1.0 and frame % 2 == 0:
            output.append("▌", style="bold #A78BFA")
    output.append("\n")

    # Particle sparkles
    if frame > 5:
        particle_line = Text("  ")
        for _ in range(random.randint(2, 5)):
            particle_line.append("  ")
            p = random.choice(PARTICLES)
            color = random.choice(GRADIENT)
            particle_line.append(p, style=f"dim {color}")
        output.append(particle_line)
        output.append("\n")

    return output


async def animate_banner(console: Console, speed: float = 0.045):
    """Play the intro reveal animation."""
    total_frames = 22

    with Live(console=console, refresh_per_second=30, transient=True) as live:
        for frame in range(total_frames):
            rendered = _render_banner_frame(frame, total_frames)
            live.update(rendered)
            await asyncio.sleep(speed)


# ─── Continuous Banner Animator ───────────────────────────────────────────────

class BannerAnimator:
    """Keeps the logo gradient animating in the top scroll-fixed area."""

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._frame: int = 0
        self._running: bool = False
        self._max_cols: int = max(len(l) for l in BANNER_LINES)

    def _render_ansi_frame(self) -> str:
        """Build raw ANSI string to redraw the banner area at the top."""
        buf = []
        buf.append("\033[s")          # save cursor position
        buf.append("\033[1;1H")       # jump to row 1, col 1

        # Row 1: empty line
        buf.append("\033[K\n")

        # Rows 2-7: logo with animated gradient
        for row, line in enumerate(BANNER_LINES):
            for col, ch in enumerate(line):
                color = _wave_color(col, self._frame - row * 2, self._max_cols)
                r, g, b = _hex_to_rgb(color)
                buf.append(f"\033[1;38;2;{r};{g};{b}m{ch}")
            buf.append("\033[0m\033[K\n")

        # Row 8: subtitle with shifting gradient
        buf.append("  ")
        for i, ch in enumerate(SUBTITLE):
            phase = (i / len(SUBTITLE) + self._frame * 0.03) % 1.0
            idx = phase * len(GRADIENT)
            gi = int(idx) % len(GRADIENT)
            gj = (gi + 1) % len(GRADIENT)
            gt = idx - int(idx)
            color = _lerp_color(GRADIENT[gi], GRADIENT[gj], gt)
            r, g, b = _hex_to_rgb(color)
            buf.append(f"\033[2;38;2;{r};{g};{b}m{ch}")
        buf.append("\033[0m\033[K\n")

        # Row 9: thin separator line
        term_w = shutil.get_terminal_size().columns
        sep_color = _wave_color(0, self._frame, 20)
        r, g, b = _hex_to_rgb(sep_color)
        buf.append(f"\033[2;38;2;{r};{g};{b}m")
        buf.append("─" * term_w)
        buf.append("\033[0m\033[K")

        buf.append("\033[u")          # restore cursor position
        return "".join(buf)

    async def _loop(self):
        """Background loop that redraws the banner."""
        while self._running:
            try:
                frame_data = self._render_ansi_frame()
                sys.stdout.write(frame_data)
                sys.stdout.flush()
                self._frame += 1
                await asyncio.sleep(0.09)
            except Exception:
                await asyncio.sleep(0.5)

    def start(self):
        """Set up the scroll region and start the background animation task."""
        term_h = shutil.get_terminal_size().lines

        # Move cursor to top and print empty banner area to claim the space
        sys.stdout.write(f"\033[1;1H")
        for _ in range(BANNER_HEIGHT):
            sys.stdout.write("\033[K\n")

        # Set scroll region: rows below the banner can scroll freely
        sys.stdout.write(f"\033[{BANNER_HEIGHT + 1};{term_h}r")
        # Move cursor into the scroll region
        sys.stdout.write(f"\033[{BANNER_HEIGHT + 1};1H")
        sys.stdout.flush()

        self._running = True
        self._task = asyncio.get_event_loop().create_task(self._loop())

    def stop(self):
        """Stop animation and reset terminal scroll region."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()

        # Reset scroll region to full terminal
        sys.stdout.write("\033[r")
        sys.stdout.flush()

    def handle_resize(self):
        """Update scroll region on terminal resize."""
        if not self._running:
            return
        term_h = shutil.get_terminal_size().lines
        sys.stdout.write(f"\033[{BANNER_HEIGHT + 1};{term_h}r")
        sys.stdout.flush()


# Global animator instance
banner_animator = BannerAnimator()


# ─── Loading Animation ───────────────────────────────────────────────────────

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


async def animate_loading(console: Console, message: str, duration: float = 1.5):
    """Show a loading spinner animation."""
    frames = int(duration / 0.08)
    with Live(console=console, refresh_per_second=15, transient=True) as live:
        for i in range(frames):
            spinner = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
            color = _wave_color(i, i, 20)
            text = Text()
            text.append(f"  {spinner} ", style=f"bold {color}")
            text.append(message, style="dim white")
            live.update(text)
            await asyncio.sleep(0.08)


# ─── Provider Switch Animation ───────────────────────────────────────────────

async def animate_switch(console: Console, provider_name: str, color: str, icon: str):
    """Animate switching to a new provider."""
    frames_data = [
        ("⠋ Switching", 0.06),
        ("⠙ Switching.", 0.06),
        ("⠹ Switching..", 0.06),
        ("⠸ Switching...", 0.06),
        (f"✓ {icon} {provider_name}", 0.0),
    ]
    with Live(console=console, refresh_per_second=15, transient=True) as live:
        for text_str, delay in frames_data:
            text = Text()
            text.append(f"  {text_str}", style=f"bold {color}")
            live.update(text)
            if delay:
                await asyncio.sleep(delay)

    console.print(f"  [bold {color}]✓ {icon} {provider_name}[/]")


# ─── Welcome Fade-In ─────────────────────────────────────────────────────────

async def animate_welcome_table(console: Console, table) -> None:
    """Animate the welcome config table appearing."""
    await asyncio.sleep(0.15)
    console.print(table)
    console.print()


# ─── Test Connection Animation ────────────────────────────────────────────────

async def animate_test_progress(console: Console, name: str, color: str, icon: str) -> Live:
    """Show animated testing indicator."""
    for i in range(6):
        t = Text()
        t.append(f"  {icon} {name:<10}  ", style=f"bold {color}")
        t.append("testing ", style="dim")
        sc = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
        t.append(f"{sc} ", style=f"bold {_wave_color(i, i, 10)}")
        console.print(t, end="\r")
        await asyncio.sleep(0.1)
