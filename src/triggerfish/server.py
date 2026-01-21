"""LSP server implementation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Optional

from lsprotocol.types import (
    CompletionList,
    CompletionOptions,
    CompletionParams,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    InitializeParams,
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind,
)
from pygls.lsp.server import LanguageServer
from pygls.uris import to_fs_path

from .completion_handler import CompletionHandler
from .config import TriggerfishConfig
from .symbol_index import Symbol, SymbolIndex, SymbolKind


_IGNORED_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".nox",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "dist",
        "build",
    }
)


class TriggerfishLanguageServer(LanguageServer):
    """Language Server for Triggerfish."""

    def __init__(self, config: TriggerfishConfig) -> None:
        super().__init__("triggerfish", "0.1.0")
        self.config = config
        self.index = SymbolIndex()
        self.completion = CompletionHandler(self.index, config)
        self._workspace_root: Optional[Path] = None
        self._setup_logging()
        self._register_handlers()

    def _setup_logging(self) -> None:
        logging.basicConfig(
            filename=str(self.config.log_file),
            level=getattr(logging, self.config.log_level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)s %(message)s",
        )

    def _register_handlers(self) -> None:
        @self.feature("initialize")
        async def initialize(params: InitializeParams) -> InitializeResult:
            self._workspace_root = _get_workspace_root(params)
            if self._workspace_root:
                await self._index_workspace(self._workspace_root)
            capabilities = ServerCapabilities(
                text_document_sync=TextDocumentSyncKind.Incremental,
                completion_provider=CompletionOptions(
                    trigger_characters=[CompletionHandler.FILE_TRIGGER]
                ),
            )
            return InitializeResult(capabilities=capabilities)

        @self.feature("initialized")
        async def initialized(_params) -> None:
            logging.info("Triggerfish LSP initialized")

        @self.feature("textDocument/didOpen")
        async def did_open(params: DidOpenTextDocumentParams) -> None:
            file_path = Path(to_fs_path(params.text_document.uri))
            await self._index_file(file_path)

        @self.feature("textDocument/didChange")
        async def did_change(params: DidChangeTextDocumentParams) -> None:
            file_path = Path(to_fs_path(params.text_document.uri))
            await self._index_file(file_path)

        @self.feature("textDocument/completion")
        async def completion(params: CompletionParams) -> CompletionList:
            return await self._completion(params)

    async def _index_file(self, file_path: Path) -> None:
        file_symbol_name = _relative_name(self._workspace_root, file_path)
        symbol = Symbol(
            name=file_symbol_name,
            kind=SymbolKind.FILE,
            file_path=file_path,
            line=1,
        )
        self.index.update_file(file_path, [symbol])

    async def _index_workspace(self, workspace_path: Path) -> None:
        for file_path in self._walk_project_files(workspace_path):
            self._add_file_symbol(file_path)
        logging.info("Indexed workspace: %s", self.index.stats())

    async def _completion(self, params: CompletionParams) -> CompletionList:
        if not params.text_document.uri.endswith(".txt"):
            return CompletionList(is_incomplete=False, items=[])

        document = self.workspace.get_text_document(params.text_document.uri)
        line_text = ""
        if params.position.line < len(document.lines):
            line_text = document.lines[params.position.line]
        items = self.completion.get_completions(line_text, params.position.character)
        return CompletionList(is_incomplete=False, items=items)

    def _walk_project_files(self, workspace_path: Path) -> Iterable[Path]:
        """Walk all files in workspace, skipping ignored directories."""
        for item in workspace_path.iterdir():
            if item.name.startswith(".") and item.is_dir():
                continue
            if item.name in _IGNORED_DIRS:
                continue
            if item.is_file():
                yield item
            elif item.is_dir():
                yield from self._walk_project_files(item)

    def _add_file_symbol(self, file_path: Path) -> None:
        """Add a FILE symbol for @ completion without running ctags."""
        file_symbol_name = _relative_name(self._workspace_root, file_path)
        symbol = Symbol(
            name=file_symbol_name,
            kind=SymbolKind.FILE,
            file_path=file_path,
            line=1,
        )
        self.index.add_symbols([symbol])


def create_server(config: Optional[TriggerfishConfig] = None) -> TriggerfishLanguageServer:
    """Create a Triggerfish language server."""
    if config is None:
        config = TriggerfishConfig.from_env()
    return TriggerfishLanguageServer(config)


def _get_workspace_root(params: InitializeParams) -> Optional[Path]:
    if params.workspace_folders:
        folder = params.workspace_folders[0]
        return Path(to_fs_path(folder.uri))
    if params.root_uri:
        return Path(to_fs_path(params.root_uri))
    return None


def _relative_name(workspace_root: Optional[Path], file_path: Path) -> str:
    if workspace_root:
        try:
            return file_path.relative_to(workspace_root).as_posix()
        except ValueError:
            pass
    return file_path.name
