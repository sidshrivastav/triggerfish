"""Shared pytest fixtures."""

from pathlib import Path
import pytest


@pytest.fixture
def sample_python_project(tmp_path: Path) -> Path:
    project = tmp_path / "sample_project"
    project.mkdir()

    (project / "main.py").write_text(
        """
class Application:
    def run(self):
        pass

def main():
    app = Application()
    app.run()
""".lstrip()
    )

    (project / "utils.py").write_text(
        """

def helper_function():
    pass

class UtilityClass:
    def utility_method(self):
        pass
""".lstrip()
    )

    return project


@pytest.fixture
def sample_ctags_output() -> str:
    return (
        '{"_type": "tag", "name": "Application", "kind": "class", "line": 2, "path": "main.py"}\n'
        '{"_type": "tag", "name": "run", "kind": "method", "line": 3, "path": "main.py", "scope": "Application"}\n'
        '{"_type": "tag", "name": "main", "kind": "function", "line": 6, "path": "main.py"}\n'
    )
