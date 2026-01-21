"""Tests for LSP server."""

import pytest

from lsprotocol.types import (
    CompletionParams,
    Position,
    TextDocumentIdentifier,
    TextDocumentItem,
)
from pygls.workspace import Workspace

from triggerfish.config import TriggerfishConfig
from triggerfish.server import TriggerfishLanguageServer
from triggerfish.symbol_index import Symbol, SymbolKind


@pytest.mark.asyncio
async def test_index_file_adds_symbols(tmp_path) -> None:
    log_file = tmp_path / "log.txt"
    config = TriggerfishConfig(log_file=log_file)
    server = TriggerfishLanguageServer(config)
    server._workspace_root = tmp_path

    file_path = tmp_path / "main.py"
    file_path.write_text("def main():\n    pass\n")
    await server._index_file(file_path)

    symbols = server.index.get_symbols()
    assert any(symbol.name == "main.py" for symbol in symbols)


@pytest.mark.asyncio
async def test_completion_restricted_to_txt(tmp_path) -> None:
    log_file = tmp_path / "log.txt"
    config = TriggerfishConfig(log_file=log_file)
    server = TriggerfishLanguageServer(config)
    server._workspace_root = tmp_path

    # Initialize workspace for testing
    workspace = Workspace(None)
    server.protocol._workspace = workspace

    symbol = Symbol(
        name="notes.txt",
        kind=SymbolKind.FILE,
        file_path=tmp_path / "notes.txt",
        line=1,
    )
    server.index.add_symbols([symbol])

    txt_uri = (tmp_path / "notes.txt").as_uri()
    txt_doc = TextDocumentItem(uri=txt_uri, language_id="text", version=1, text="@")
    server.workspace.put_text_document(txt_doc)
    txt_params = CompletionParams(
        text_document=TextDocumentIdentifier(uri=txt_uri),
        position=Position(line=0, character=1),
    )
    txt_result = await server._completion(txt_params)
    assert txt_result.items

    py_uri = (tmp_path / "main.py").as_uri()
    py_doc = TextDocumentItem(uri=py_uri, language_id="python", version=1, text="@")
    server.workspace.put_text_document(py_doc)
    py_params = CompletionParams(
        text_document=TextDocumentIdentifier(uri=py_uri),
        position=Position(line=0, character=1),
    )
    py_result = await server._completion(py_params)
    assert not py_result.items
