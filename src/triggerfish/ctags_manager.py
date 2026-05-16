"""CTags subprocess integration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import subprocess

from .config import TriggerfishConfig


class CTagsError(RuntimeError):
    """Base error for ctags execution."""


class CTagsNotFoundError(CTagsError):
    """Raised when ctags executable is not found."""


class CTagsTimeoutError(CTagsError):
    """Raised when ctags execution times out."""


@dataclass
class CTagsManager:
    """Manage calls to universal-ctags."""

    config: TriggerfishConfig

    def generate_tags(
        self, file_path: Path, language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate tags for a file. Returns normalized tag dictionaries."""
        command = [
            self.config.ctags_executable,
            "--output-format=json",
            "--fields=*",
            "--excmd=pattern",
        ]
        if language:
            command.append(f"--language-force={language}")
        command.append(str(file_path))

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=self.config.ctags_timeout,
            )
        except FileNotFoundError as exc:
            raise CTagsNotFoundError("ctags executable not found") from exc
        except subprocess.TimeoutExpired as exc:
            raise CTagsTimeoutError("ctags timed out") from exc
        except subprocess.CalledProcessError as exc:
            raise CTagsError("ctags execution failed") from exc

        return _parse_ctags_output(completed.stdout)

    def verify_ctags_available(self) -> bool:
        """Return True if ctags is available."""
        try:
            completed = subprocess.run(
                [self.config.ctags_executable, "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=self.config.ctags_timeout,
            )
        except FileNotFoundError:
            return False
        return completed.returncode == 0


def _parse_ctags_output(stdout: str) -> List[Dict[str, Any]]:
    tags: List[Dict[str, Any]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("_type") != "tag":
            continue
        tags.append(
            {
                "name": entry.get("name"),
                "kind": entry.get("kind"),
                "line": entry.get("line"),
                "path": entry.get("path"),
                "scope": entry.get("scope"),
                "language": entry.get("language"),
            }
        )
    return tags
