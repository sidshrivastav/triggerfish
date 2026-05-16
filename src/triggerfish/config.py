"""Configuration for Triggerfish."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os


_ENV_PREFIX = "TRIGGERFISH_"


@dataclass
class TriggerfishConfig:
    """Configuration values for Triggerfish."""

    log_file: Path
    log_level: str = "INFO"
    ctags_executable: str = "ctags"
    ctags_timeout: int = 30
    min_fuzzy_score: int = 60
    max_completion_items: int = 50

    @classmethod
    def default(cls) -> "TriggerfishConfig":
        """Create default config and ensure log directory exists."""
        log_dir = Path.home() / ".triggerfish" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return cls(log_file=log_dir / "triggerfish.log")

    @classmethod
    def from_env(cls) -> "TriggerfishConfig":
        """Create config with environment variable overrides."""
        config = cls.default()
        log_level = os.getenv(f"{_ENV_PREFIX}LOG_LEVEL")
        log_file = os.getenv(f"{_ENV_PREFIX}LOG_FILE")
        ctags_executable = os.getenv(f"{_ENV_PREFIX}CTAGS_EXECUTABLE")
        ctags_timeout = _get_int_env(f"{_ENV_PREFIX}CTAGS_TIMEOUT")
        min_fuzzy_score = _get_int_env(f"{_ENV_PREFIX}MIN_FUZZY_SCORE")
        max_completion_items = _get_int_env(f"{_ENV_PREFIX}MAX_COMPLETION_ITEMS")

        if log_level:
            config.log_level = log_level
        if log_file:
            config.log_file = Path(log_file)
        if ctags_executable:
            config.ctags_executable = ctags_executable
        if ctags_timeout is not None:
            config.ctags_timeout = ctags_timeout
        if min_fuzzy_score is not None:
            config.min_fuzzy_score = min_fuzzy_score
        if max_completion_items is not None:
            config.max_completion_items = max_completion_items
        return config


def _get_int_env(name: str) -> Optional[int]:
    value = os.getenv(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None
