from __future__ import annotations

from pathlib import Path

from .config import load_kimi_config, load_minimax_config, resolve_provider
from .kimi_client import KimiClient
from .minimax_client import MinimaxClient


def create_json_client(*, env_path: str | Path | None = None, provider: str | None = None):
    selected = resolve_provider(env_path, provider)
    if selected == "moonshot":
        return KimiClient(load_kimi_config(env_path))
    if selected == "minimax":
        return MinimaxClient(load_minimax_config(env_path))
    raise ValueError(f"Unsupported LLM provider: {selected}")
