"""Symbol indexing and fuzzy search."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from rapidfuzz import fuzz, process, utils


class SymbolKind(Enum):
    """Supported symbol kinds."""

    FILE = "file"
    CLASS = "class"
    METHOD = "method"
    FUNCTION = "function"
    VARIABLE = "variable"


@dataclass(frozen=True)
class Symbol:
    """Represents a symbol within a file."""

    name: str
    kind: SymbolKind
    file_path: Path
    line: int
    scope: Optional[str] = None
    language: Optional[str] = None

    def display_name(self) -> str:
        """Return scoped display name when applicable."""
        if self.scope:
            return f"{self.scope}.{self.name}"
        return self.name


class SymbolIndex:
    """In-memory symbol index with fuzzy search."""

    def __init__(self) -> None:
        self._symbols: List[Symbol] = []
        self._by_file: Dict[Path, List[Symbol]] = {}
        self._by_kind: Dict[SymbolKind, List[Symbol]] = {}

    def add_symbols(self, symbols: Iterable[Symbol]) -> None:
        for symbol in symbols:
            self._symbols.append(symbol)
            self._by_file.setdefault(symbol.file_path, []).append(symbol)
            self._by_kind.setdefault(symbol.kind, []).append(symbol)

    def clear_file(self, file_path: Path) -> None:
        symbols = self._by_file.pop(file_path, [])
        if not symbols:
            return
        symbols_set = set(symbols)
        self._symbols = [symbol for symbol in self._symbols if symbol not in symbols_set]
        for kind, kind_symbols in list(self._by_kind.items()):
            filtered = [symbol for symbol in kind_symbols if symbol not in symbols_set]
            if filtered:
                self._by_kind[kind] = filtered
            else:
                self._by_kind.pop(kind, None)

    def update_file(self, file_path: Path, symbols: Iterable[Symbol]) -> None:
        self.clear_file(file_path)
        self.add_symbols(symbols)

    def get_symbols(self, kind: Optional[SymbolKind] = None) -> List[Symbol]:
        if kind is None:
            return list(self._symbols)
        return list(self._by_kind.get(kind, []))

    def fuzzy_search(
        self,
        query: str,
        kind: Optional[SymbolKind] = None,
        limit: int = 50,
        min_score: int = 60,
    ) -> List[Tuple[Symbol, float]]:
        """Fuzzy search using rapidfuzz."""
        candidates = self.get_symbols(kind)
        if not candidates:
            return []
        choices = [symbol.display_name() for symbol in candidates]
        results = process.extract(
            query,
            choices,
            scorer=fuzz.WRatio,
            processor=utils.default_process,
            score_cutoff=min_score,
            limit=limit,
        )
        matches: List[Tuple[Symbol, float]] = []
        for _match, score, index in results:
            matches.append((candidates[index], float(score)))
        return matches

    def stats(self) -> Dict[str, int]:
        stats: Dict[str, int] = {"total": len(self._symbols)}
        for kind, symbols in self._by_kind.items():
            stats[kind.value] = len(symbols)
        return stats
