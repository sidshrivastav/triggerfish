"""Completion logic for Triggerfish."""

from __future__ import annotations

from typing import List, Optional, Tuple

from lsprotocol.types import CompletionItem, CompletionItemKind

from .config import TriggerfishConfig
from .symbol_index import Symbol, SymbolIndex, SymbolKind


class CompletionHandler:
    """Handles trigger-based completion requests."""

    def __init__(
        self,
        symbol_index: SymbolIndex,
        config: TriggerfishConfig,
        trigger: str,
        symbol_kinds: List[SymbolKind],
        completion_kind: CompletionItemKind,
    ) -> None:
        self._index = symbol_index
        self._config = config
        self._trigger = trigger
        self._symbol_kinds = symbol_kinds
        self._completion_kind = completion_kind

    def should_trigger(self, line: str, character: int) -> bool:
        return line.rfind(self._trigger, 0, character) != -1

    def parse_query(self, line: str, character: int) -> Optional[str]:
        trigger_index = line.rfind(self._trigger, 0, character)
        if trigger_index == -1:
            return None
        query = line[trigger_index + 1 : character]
        if not query:
            return ""
        if any(char.isspace() for char in query):
            return None
        return query

    def get_completions(self, line: str, character: int) -> List[CompletionItem]:
        query = self.parse_query(line, character)
        if query is None:
            return []

        # Collect symbols from all kinds
        all_matches: List[Tuple[Symbol, float]] = []

        if query == "":
            # For empty query, get all symbols from all specified kinds
            for kind in self._symbol_kinds:
                symbols = self._index.get_symbols(kind)
                all_matches.extend([(symbol, 0.0) for symbol in symbols])
            # Limit to max_completion_items
            all_matches = all_matches[: self._config.max_completion_items]
        else:
            # For non-empty query, search across all specified kinds
            for kind in self._symbol_kinds:
                matches = self._index.fuzzy_search(
                    query,
                    kind=kind,
                    limit=self._config.max_completion_items,
                    min_score=self._config.min_fuzzy_score,
                )
                all_matches.extend(matches)
            # Sort by score descending and limit
            all_matches.sort(key=lambda x: x[1], reverse=True)
            all_matches = all_matches[: self._config.max_completion_items]

        return [self._to_completion_item(symbol, score) for symbol, score in all_matches]

    def _to_completion_item(self, symbol: Symbol, score: float) -> CompletionItem:
        sort_text = f"{100 - int(score):03d}"
        return CompletionItem(
            label=symbol.name,
            kind=self._completion_kind,
            detail=f"{symbol.kind.value} at {symbol.file_path}:{symbol.line}",
            sort_text=sort_text,
            insert_text=symbol.name,
        )
