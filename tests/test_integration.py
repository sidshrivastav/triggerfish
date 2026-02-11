"""Integration-style tests."""

from pathlib import Path

from lsprotocol.types import CompletionItemKind

from triggerfish.completion_handler import CompletionHandler
from triggerfish.config import TriggerfishConfig
from triggerfish.symbol_index import Symbol, SymbolIndex, SymbolKind


def test_completion_flow() -> None:
    index = SymbolIndex()
    index.add_symbols(
        [
            Symbol(name="my_file.py", kind=SymbolKind.FILE, file_path=Path("/tmp/my_file.py"), line=1),
            Symbol(name="my_first.js", kind=SymbolKind.FILE, file_path=Path("/tmp/my_first.js"), line=1),
            Symbol(name="other.txt", kind=SymbolKind.FILE, file_path=Path("/tmp/other.txt"), line=1),
        ]
    )
    config = TriggerfishConfig(log_file=Path("/tmp/log.txt"))
    handler = CompletionHandler(index, config, "@", [SymbolKind.FILE], CompletionItemKind.File)

    completions = handler.get_completions("@myfi", len("@myfi"))
    labels = [item.label for item in completions]
    assert "my_file.py" in labels
    assert "my_first.js" in labels
