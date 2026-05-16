"""Tests for ctags manager."""

from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired

import pytest

from triggerfish.config import TriggerfishConfig
from triggerfish.ctags_manager import (
    CTagsManager,
    CTagsTimeoutError,
)


def test_generate_tags_parses_json(sample_ctags_output, monkeypatch, tmp_path) -> None:
    config = TriggerfishConfig(log_file=tmp_path / "log.txt")
    manager = CTagsManager(config)

    def fake_run(*_args, **_kwargs):
        return CompletedProcess(args=["ctags"], returncode=0, stdout=sample_ctags_output, stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    tags = manager.generate_tags(Path("main.py"))
    assert len(tags) == 3
    assert tags[0]["name"] == "Application"


def test_generate_tags_timeout(monkeypatch, tmp_path) -> None:
    config = TriggerfishConfig(log_file=tmp_path / "log.txt")
    manager = CTagsManager(config)

    def fake_run(*_args, **_kwargs):
        raise TimeoutExpired(cmd="ctags", timeout=1)

    monkeypatch.setattr("subprocess.run", fake_run)
    with pytest.raises(CTagsTimeoutError):
        manager.generate_tags(Path("main.py"))


def test_verify_ctags_available(monkeypatch, tmp_path) -> None:
    config = TriggerfishConfig(log_file=tmp_path / "log.txt")
    manager = CTagsManager(config)

    def fake_run(*_args, **_kwargs):
        return CompletedProcess(args=["ctags"], returncode=0, stdout="ctags", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    assert manager.verify_ctags_available()
