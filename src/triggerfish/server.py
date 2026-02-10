"""LSP server implementation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List, Optional

from lsprotocol.types import (
    CompletionItemKind,
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
from .ctags_manager import CTagsManager, CTagsError
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
        self.ctags = CTagsManager(config)

        # Create completion handlers for different triggers
        self.file_completion = CompletionHandler(
            self.index, config, "@", [SymbolKind.FILE], CompletionItemKind.File
        )
        self.class_completion = CompletionHandler(
            self.index, config, ".", [SymbolKind.CLASS], CompletionItemKind.Class
        )
        self.method_completion = CompletionHandler(
            self.index, config, "#", [SymbolKind.METHOD, SymbolKind.FUNCTION], CompletionItemKind.Method
        )

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
                    trigger_characters=["@", ".", "#"]
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
        symbols = [
            Symbol(
                name=file_symbol_name,
                kind=SymbolKind.FILE,
                file_path=file_path,
                line=1,
            )
        ]

        # Also parse code symbols if ctags is available
        code_symbols = self._parse_code_symbols(file_path)
        if code_symbols:
            symbols.extend(code_symbols)

        self.index.update_file(file_path, symbols)

    async def _index_workspace(self, workspace_path: Path) -> None:
        for file_path in self._walk_project_files(workspace_path):
            self._add_file_symbol(file_path)
            # Also parse code symbols from each file
            code_symbols = self._parse_code_symbols(file_path)
            if code_symbols:
                self.index.add_symbols(code_symbols)
        logging.info("Indexed workspace: %s", self.index.stats())

    async def _completion(self, params: CompletionParams) -> CompletionList:
        if not params.text_document.uri.endswith(".txt"):
            return CompletionList(is_incomplete=False, items=[])

        document = self.workspace.get_text_document(params.text_document.uri)
        line_text = ""
        if params.position.line < len(document.lines):
            line_text = document.lines[params.position.line]

        # Check which trigger was used and route to appropriate handler
        handlers = [
            self.file_completion,
            self.class_completion,
            self.method_completion,
        ]

        for handler in handlers:
            if handler.should_trigger(line_text, params.position.character):
                items = handler.get_completions(line_text, params.position.character)
                return CompletionList(is_incomplete=False, items=items)

        return CompletionList(is_incomplete=False, items=[])

    def _parse_code_symbols(self, file_path: Path) -> List[Symbol]:
        """Parse code symbols (class, method, function) from a file using ctags."""
        try:
            tags = self.ctags.generate_tags(file_path)
        except CTagsError:
            # If ctags fails, just return empty list (file is still indexed)
            return []

        symbols: List[Symbol] = []
        for tag in tags:
            # Map ctags kind to our SymbolKind
            kind = _map_ctags_kind(tag.get("kind"))
            if kind is None:
                continue

            symbols.append(
                Symbol(
                    name=tag.get("name", ""),
                    kind=kind,
                    file_path=file_path,
                    line=tag.get("line", 1),
                    scope=tag.get("scope"),
                    language=tag.get("language"),
                )
            )

        return symbols

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


def _map_ctags_kind(ctags_kind: Optional[str]) -> Optional[SymbolKind]:
    """Map ctags kind string to SymbolKind."""
    if not ctags_kind:
        return None

    # Map common ctags kinds to our SymbolKind
    kind_mapping = {
        # Classes
        "class": SymbolKind.CLASS,
        "interface": SymbolKind.CLASS,
        "struct": SymbolKind.CLASS,
        "enum": SymbolKind.CLASS,
        "type": SymbolKind.CLASS,
        # Methods
        "method": SymbolKind.METHOD,
        "member": SymbolKind.METHOD,
        # Functions
        "function": SymbolKind.FUNCTION,
        "func": SymbolKind.FUNCTION,
        "procedure": SymbolKind.FUNCTION,
        "subroutine": SymbolKind.FUNCTION,
        # Variables
        "variable": SymbolKind.VARIABLE,
        "var": SymbolKind.VARIABLE,
        "field": SymbolKind.VARIABLE,
        "constant": SymbolKind.VARIABLE,
    }

    return kind_mapping.get(ctags_kind.lower())
