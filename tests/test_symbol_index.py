"""Tests for symbol indexing."""

from pathlib import Path

from triggerfish.symbol_index import Symbol, SymbolIndex, SymbolKind


def test_add_and_search_symbols() -> None:
    index = SymbolIndex()
    symbols = [
        Symbol(name="utils.py", kind=SymbolKind.FILE, file_path=Path("/tmp/utils.py"), line=1),
        Symbol(name="main.py", kind=SymbolKind.FILE, file_path=Path("/tmp/main.py"), line=1),
    ]
    index.add_symbols(symbols)

    matches = index.fuzzy_search("util", kind=SymbolKind.FILE)
    assert matches
    assert matches[0][0].name == "utils.py"


def test_clear_file_removes_symbols() -> None:
    index = SymbolIndex()
    file_path = Path("/tmp/main.py")
    index.add_symbols(
        [Symbol(name="main.py", kind=SymbolKind.FILE, file_path=file_path, line=1)]
    )
    index.clear_file(file_path)
    assert not index.get_symbols(SymbolKind.FILE)


def test_stats_counts() -> None:
    index = SymbolIndex()
    index.add_symbols(
        [Symbol(name="main.py", kind=SymbolKind.FILE, file_path=Path("/tmp/main.py"), line=1)]
    )
    stats = index.stats()
    assert stats["total"] == 1
    assert stats["file"] == 1
