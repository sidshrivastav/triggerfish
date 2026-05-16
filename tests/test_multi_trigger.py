"""Tests for multiple trigger support (., #, @)."""

from pathlib import Path

from lsprotocol.types import CompletionItemKind

from triggerfish.completion_handler import CompletionHandler
from triggerfish.config import TriggerfishConfig
from triggerfish.symbol_index import Symbol, SymbolIndex, SymbolKind


def test_class_trigger_with_dot() -> None:
    """Test . trigger for class completions."""
    index = SymbolIndex()
    index.add_symbols(
        [
            Symbol(name="MyClass", kind=SymbolKind.CLASS, file_path=Path("/tmp/main.py"), line=10),
            Symbol(name="UtilityClass", kind=SymbolKind.CLASS, file_path=Path("/tmp/utils.py"), line=5),
            Symbol(name="BaseClass", kind=SymbolKind.CLASS, file_path=Path("/tmp/base.py"), line=1),
        ]
    )
    config = TriggerfishConfig(log_file=Path("/tmp/log.txt"))
    handler = CompletionHandler(index, config, ".", [SymbolKind.CLASS], CompletionItemKind.Class)

    # Test trigger detection
    line = "extends .MyClass"
    assert handler.should_trigger(line, len(line))
    assert handler.parse_query(line, len(line)) == "MyClass"

    # Test completions
    completions = handler.get_completions(".Util", len(".Util"))
    assert len(completions) > 0
    assert completions[0].label == "UtilityClass"
    assert completions[0].kind == CompletionItemKind.Class


def test_method_trigger_with_hash() -> None:
    """Test # trigger for method/function completions."""
    index = SymbolIndex()
    index.add_symbols(
        [
            Symbol(name="get_user", kind=SymbolKind.FUNCTION, file_path=Path("/tmp/api.py"), line=15),
            Symbol(name="save_data", kind=SymbolKind.METHOD, file_path=Path("/tmp/db.py"), line=25),
            Symbol(name="calculate_sum", kind=SymbolKind.FUNCTION, file_path=Path("/tmp/math.py"), line=8),
        ]
    )
    config = TriggerfishConfig(log_file=Path("/tmp/log.txt"))
    handler = CompletionHandler(
        index, config, "#", [SymbolKind.METHOD, SymbolKind.FUNCTION], CompletionItemKind.Method
    )

    # Test trigger detection
    line = "call #get_user"
    assert handler.should_trigger(line, len(line))
    assert handler.parse_query(line, len(line)) == "get_user"

    # Test completions with fuzzy search
    completions = handler.get_completions("#save", len("#save"))
    assert len(completions) > 0
    assert completions[0].label == "save_data"
    assert completions[0].kind == CompletionItemKind.Method


def test_all_triggers_independently() -> None:
    """Test that all three triggers work independently."""
    index = SymbolIndex()
    index.add_symbols(
        [
            Symbol(name="utils.py", kind=SymbolKind.FILE, file_path=Path("/tmp/utils.py"), line=1),
            Symbol(name="MyClass", kind=SymbolKind.CLASS, file_path=Path("/tmp/main.py"), line=10),
            Symbol(name="my_function", kind=SymbolKind.FUNCTION, file_path=Path("/tmp/utils.py"), line=20),
        ]
    )
    config = TriggerfishConfig(log_file=Path("/tmp/log.txt"))

    # Create three different handlers
    file_handler = CompletionHandler(index, config, "@", [SymbolKind.FILE], CompletionItemKind.File)
    class_handler = CompletionHandler(index, config, ".", [SymbolKind.CLASS], CompletionItemKind.Class)
    method_handler = CompletionHandler(
        index, config, "#", [SymbolKind.METHOD, SymbolKind.FUNCTION], CompletionItemKind.Method
    )

    # Test file completions with @
    file_completions = file_handler.get_completions("@util", len("@util"))
    assert len(file_completions) > 0
    assert file_completions[0].label == "utils.py"

    # Test class completions with .
    class_completions = class_handler.get_completions(".MyCl", len(".MyCl"))
    assert len(class_completions) > 0
    assert class_completions[0].label == "MyClass"

    # Test method/function completions with #
    method_completions = method_handler.get_completions("#my_func", len("#my_func"))
    assert len(method_completions) > 0
    assert method_completions[0].label == "my_function"


def test_empty_query_returns_all_symbols() -> None:
    """Test that typing just the trigger returns all symbols of that kind."""
    index = SymbolIndex()
    index.add_symbols(
        [
            Symbol(name="ClassA", kind=SymbolKind.CLASS, file_path=Path("/tmp/a.py"), line=1),
            Symbol(name="ClassB", kind=SymbolKind.CLASS, file_path=Path("/tmp/b.py"), line=1),
            Symbol(name="ClassC", kind=SymbolKind.CLASS, file_path=Path("/tmp/c.py"), line=1),
        ]
    )
    config = TriggerfishConfig(log_file=Path("/tmp/log.txt"))
    handler = CompletionHandler(index, config, ".", [SymbolKind.CLASS], CompletionItemKind.Class)

    # Just typing "." should return all classes
    completions = handler.get_completions(".", len("."))
    assert len(completions) == 3
    labels = {c.label for c in completions}
    assert labels == {"ClassA", "ClassB", "ClassC"}
