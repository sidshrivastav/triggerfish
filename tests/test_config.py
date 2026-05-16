"""Tests for configuration."""

from pathlib import Path

from triggerfish.config import TriggerfishConfig


def test_default_creates_log_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    config = TriggerfishConfig.default()
    assert config.log_file.parent.exists()


def test_env_overrides(tmp_path, monkeypatch) -> None:
    log_file = tmp_path / "custom.log"
    monkeypatch.setenv("TRIGGERFISH_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("TRIGGERFISH_LOG_FILE", str(log_file))
    monkeypatch.setenv("TRIGGERFISH_CTAGS_TIMEOUT", "55")
    monkeypatch.setenv("TRIGGERFISH_MIN_FUZZY_SCORE", "70")
    monkeypatch.setenv("TRIGGERFISH_MAX_COMPLETION_ITEMS", "25")

    config = TriggerfishConfig.from_env()
    assert config.log_level == "DEBUG"
    assert config.log_file == Path(log_file)
    assert config.ctags_timeout == 55
    assert config.min_fuzzy_score == 70
    assert config.max_completion_items == 25
