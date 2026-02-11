# Triggerfish LSP - Developer Guide

This document provides implementation details and architecture overview for developers working on Triggerfish LSP.

## Architecture Overview

### Core Components

```
┌──────────────────────────────────────────────────────────┐
│                    LSP Client (Editor)                    │
│              (VSCode, Neovim, Zed, etc.)                  │
└────────────────────────┬─────────────────────────────────┘
                         │ LSP Protocol (stdio)
┌────────────────────────▼─────────────────────────────────┐
│        TriggerfishLanguageServer (server.py)             │
│  • Handles LSP protocol events                           │
│  • Manages workspace indexing                            │
│  • Routes completion requests                            │
└────────────────┬──────────────────────┬──────────────────┘
                 │                      │
      ┌──────────▼─────────┐    ┌──────▼──────────────┐
      │  SymbolIndex       │    │ CompletionHandler   │
      │  (symbol_index.py) │    │ (completion_handler)│
      │                    │    │                     │
      │ • add_symbols()    │    │ • should_trigger()  │
      │ • fuzzy_search()   │    │ • parse_query()     │
      │ • get_symbols()    │    │ • get_completions() │
      └────────────────────┘    └──────────────────────┘
             ▲                            │
             │                            │
      ┌──────┴────────────────────────────┘
      │
      │   CTagsManager (ctags_manager.py)
      │   • Calls universal-ctags
      │   • Parses JSON output
      └───────────────────────────────────────┘
```

## File Structure

```
src/triggerfish/
├── __init__.py          # Package init
├── __main__.py          # CLI entry point
├── server.py            # LSP server implementation (190 lines)
├── completion_handler.py # Generic completion logic (76 lines)
├── symbol_index.py      # In-memory symbol storage (107 lines)
├── ctags_manager.py     # CTags integration (101 lines)
└── config.py            # Configuration management (66 lines)

tests/
├── test_server.py
├── test_completion_handler.py
├── test_symbol_index.py
├── test_ctags_manager.py
├── test_config.py
├── test_integration.py
└── test_multi_trigger.py  # Tests for @, ., # triggers
```

## Key Implementation Details

### 1. CompletionHandler (completion_handler.py)

Generic handler that supports multiple triggers and symbol kinds:

```python
handler = CompletionHandler(
    index=symbol_index,
    config=config,
    trigger="@",                    # Character to trigger completions
    symbol_kinds=[SymbolKind.FILE], # Types of symbols to search
    completion_kind=CompletionItemKind.File  # LSP completion type
)
```

**Features:**
- Parses query text after trigger character
- Rejects queries with whitespace
- Fuzzy search using `rapidfuzz.WRatio`
- Returns sorted completions by score

### 2. SymbolIndex (symbol_index.py)

In-memory index with three data structures for fast lookup:

```python
self._symbols: List[Symbol]                  # All symbols in order
self._by_file: Dict[Path, List[Symbol]]     # Index by file path
self._by_kind: Dict[SymbolKind, List[Symbol]]  # Index by kind
```

**Symbol Types:**
- `FILE`: File paths (for `@` trigger)
- `CLASS`: Class definitions (for `.` trigger)
- `METHOD`: Class methods (for `#` trigger)
- `FUNCTION`: Standalone functions (for `#` trigger)
- `VARIABLE`: Variables (not currently used)

### 3. CTags Integration (server.py)

**Symbol Parsing Flow:**

1. During workspace initialization, iterate all project files
2. For each file, call `_parse_code_symbols(file_path)`
3. Execute `ctags --output-format=json` on the file
4. Parse JSON output and map kinds to `SymbolKind`
5. Add symbols to the index

**Kind Mapping:**

```python
ctags_kind -> SymbolKind
"class"     -> CLASS
"interface" -> CLASS
"struct"    -> CLASS
"method"    -> METHOD
"function"  -> FUNCTION
"func"      -> FUNCTION
```

### 4. Completion Routing (server.py)

When a completion request arrives:

1. Check if file ends with `.txt` (restriction)
2. Get line text at cursor position
3. Try each handler in order (file, class, method)
4. First matching trigger wins
5. Return completions from matched handler

## Adding a New Trigger

To add a new trigger (e.g., `$` for variables):

1. **Create handler** in `server.py.__init__()`:
```python
self.variable_completion = CompletionHandler(
    self.index, config, "$",
    [SymbolKind.VARIABLE],
    CompletionItemKind.Variable
)
```

2. **Register trigger** in `_register_handlers()`:
```python
completion_provider=CompletionOptions(
    trigger_characters=["@", ".", "#", "$"]
)
```

3. **Add to routing** in `_completion()`:
```python
handlers = [
    self.file_completion,
    self.class_completion,
    self.method_completion,
    self.variable_completion,  # New handler
]
```

4. **Update ctags mapping** in `_map_ctags_kind()`:
```python
"variable": SymbolKind.VARIABLE,
"var": SymbolKind.VARIABLE,
```

## Extending File Type Support

Currently restricted to `.txt` files at `server.py:130-131`:

```python
if not params.text_document.uri.endswith(".txt"):
    return CompletionList(is_incomplete=False, items=[])
```

To enable in code files:

1. **Option A - Remove restriction entirely:**
```python
# Delete the check, allow all filetypes
```

2. **Option B - Whitelist specific extensions:**
```python
ALLOWED_EXTENSIONS = {".txt", ".md", ".rst", ".org"}
ext = Path(params.text_document.uri).suffix
if ext not in ALLOWED_EXTENSIONS:
    return CompletionList(is_incomplete=False, items=[])
```

3. **Option C - Different triggers per filetype:**
```python
if uri.endswith(".txt"):
    handlers = [file, class, method]  # All triggers
elif uri.endswith((".py", ".js", ".ts")):
    handlers = [class, method]  # Only . and #
else:
    return CompletionList(is_incomplete=False, items=[])
```

## Performance Considerations

### Workspace Indexing

- **Initial indexing:** O(n) where n = number of files
- **Per-file ctags:** ~50-200ms for typical code files
- **Large projects:** May take 10-30 seconds for full index

**Optimizations:**
- Ignored directories: `.git`, `node_modules`, `__pycache__`, etc.
- Parallel indexing: Not yet implemented
- Incremental updates: On file open/change only

### Fuzzy Search

- **Algorithm:** `rapidfuzz.WRatio` (weighted ratio)
- **Complexity:** O(m*n) where m = query length, n = symbol count
- **Typical time:** <1ms for queries on 10k symbols

**Optimizations:**
- Search filtered by `SymbolKind` first
- Limited to `max_completion_items` (default 50)
- Score cutoff at `min_fuzzy_score` (default 60)

### Memory Usage

- **Per symbol:** ~200 bytes (Symbol dataclass)
- **10k symbols:** ~2 MB
- **100k symbols:** ~20 MB

## Testing Strategy

### Unit Tests

- `test_symbol_index.py`: Symbol storage and search
- `test_completion_handler.py`: Completion logic
- `test_ctags_manager.py`: CTags parsing
- `test_config.py`: Configuration

### Integration Tests

- `test_integration.py`: End-to-end completion flow
- `test_server.py`: LSP server functions
- `test_multi_trigger.py`: Multiple triggers (@, ., #)

### Coverage

Current coverage: >80%

```bash
pytest --cov=src/triggerfish --cov-report=html
```

## Development Workflow

### Running in Development

```bash
# Install in editable mode
nix-shell --run "pip install -e ."

# Run with debug logging
python -m triggerfish --log-level DEBUG

# Watch logs
tail -f ~/.triggerfish/logs/triggerfish.log
```

### Testing Changes

```bash
# Run all tests
nix-shell --run "pytest tests/ -v"

# Run specific test
nix-shell --run "pytest tests/test_multi_trigger.py -v"

# Run with coverage
nix-shell --run "pytest --cov=src/triggerfish --cov-report=term"
```

### Code Quality

```bash
# Format code
nix-shell --run "black src/ tests/"

# Type check
nix-shell --run "mypy src/"

# Lint
nix-shell --run "ruff check src/ tests/"
```

## Editor Integration Development

### Testing with Neovim

```lua
-- Minimal test config
vim.lsp.config.triggerfish = {
  cmd = { 'python3', '-m', 'triggerfish', '--log-level', 'DEBUG' },
  filetypes = { 'text' },
  root_markers = { '.git' },
}

vim.api.nvim_create_autocmd('FileType', {
  pattern = 'text',
  callback = function(args)
    vim.lsp.enable('triggerfish', args.buf)
  end,
})
```

Check status:
```vim
:LspInfo
:LspLog
```

### Testing with VSCode

1. Enable LSP logging in settings:
```json
"lsp.trace.server": "verbose"
```

2. View logs in Output panel → "Triggerfish LSP"

### Testing with Zed

Check debug panel for LSP communication logs.

## Common Pitfalls

### 1. CTags Not Found

**Symptom:** No class/method completions
**Solution:**
- Install `universal-ctags` (not `exuberant-ctags`)
- Verify: `ctags --version` should show "Universal Ctags"

### 2. Trigger Not Working

**Symptom:** Completions don't appear
**Solution:**
- Check trigger is registered in `completion_provider`
- Verify handler is added to routing list
- Check logs for trigger detection

### 3. Wrong Symbols Returned

**Symptom:** Method completions show classes
**Solution:**
- Check `symbol_kinds` parameter in handler creation
- Verify ctags kind mapping in `_map_ctags_kind()`

### 4. Performance Issues

**Symptom:** Slow completions or indexing
**Solution:**
- Check ctags timeout setting
- Verify ignored directories are configured
- Consider reducing `max_completion_items`

## Future Enhancements

### Planned Features

- [ ] Scope-aware completions (methods scoped to classes)
- [ ] Parallel workspace indexing
- [ ] Incremental ctags parsing
- [ ] Context-aware triggers (only show relevant symbols)
- [ ] Multi-file symbol references
- [ ] Symbol documentation in completions
- [ ] Go-to-definition support
- [ ] Hover information

### Extension Points

**Custom Symbol Providers:**
```python
class SymbolProvider(Protocol):
    def get_symbols(self, file_path: Path) -> List[Symbol]: ...
```

**Custom Fuzzy Matchers:**
```python
class FuzzyMatcher(Protocol):
    def search(self, query: str, choices: List[str]) -> List[Tuple[str, float]]: ...
```

## License

Apache 2.0
