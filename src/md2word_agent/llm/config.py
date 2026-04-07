from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

SUPPORTED_PROVIDERS = {"moonshot", "minimax"}


@dataclass(slots=True)
class KimiConfig:
    api_key: str
    base_url: str
    model: str
    temperature: float = 0.0


@dataclass(slots=True)
class MinimaxConfig:
    api_key: str
    base_url: str
    model: str
    temperature: float = 1.0


def _read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _load_env(env_path: str | Path | None = None) -> dict[str, str]:
    path = Path(env_path) if env_path else Path.cwd() / ".env"
    file_values = _read_dotenv(path)
    return {**file_values, **os.environ}


def resolve_provider(env_path: str | Path | None = None, provider: str | None = None) -> str:
    selected = (provider or _load_env(env_path).get("LLM_PROVIDER", "moonshot")).strip().lower()
    if selected == "kimi":
        selected = "moonshot"
    if selected not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported LLM provider: {selected}")
    return selected


def load_kimi_config(env_path: str | Path | None = None) -> KimiConfig:
    merged = _load_env(env_path)
    return KimiConfig(
        api_key=merged.get("MOONSHOT_API_KEY", ""),
        base_url=merged.get("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1"),
        model=merged.get("MOONSHOT_MODEL", "kimi-k2.5"),
        temperature=float(merged.get("MOONSHOT_TEMPERATURE", "0") or 0),
    )


def load_minimax_config(env_path: str | Path | None = None) -> MinimaxConfig:
    merged = _load_env(env_path)
    return MinimaxConfig(
        api_key=merged.get("MINIMAX_API_KEY", ""),
        base_url=merged.get("MINIMAX_BASE_URL", "https://api.minimax.io/v1"),
        model=merged.get("MINIMAX_MODEL", "MiniMax-M2.5"),
        temperature=float(merged.get("MINIMAX_TEMPERATURE", "1.0") or 1.0),
    )
