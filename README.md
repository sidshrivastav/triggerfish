# Triggerfish LSP

Lightning-fast LSP server with smart trigger-based file completions.

## Features

- `@` trigger for file completions with fuzzy search in `.txt` files
- Shows all project files (not just code files)
- Automatic workspace indexing with intelligent directory filtering

## Requirements

- Python 3.9+

## Installation

```bash
# From source
pip install -e .

# From PyPI (future)
pip install triggerfish
```

## Usage

```bash
# Start server
python -m triggerfish

# With debug logging
python -m triggerfish --log-level DEBUG
```

## Editor Configuration

### Generic LSP Client

- Command: `python -m triggerfish`
- Trigger character: `@`

### VSCode

Example `settings.json` snippet:

```json
{
  "triggerfish.command": "python",
  "triggerfish.args": ["-m", "triggerfish"],
  "triggerfish.triggerCharacters": ["@"]
}
```

### Neovim

```lua
-- Triggerfish LSP setup using vim.lsp.config
vim.lsp.config.triggerfish = {
  cmd = { 'python', '-m', 'triggerfish' },
  filetypes = { 'text' },  -- Only works in .txt files
  root_markers = { '.git' },
}

-- Enable triggerfish for text files
vim.api.nvim_create_autocmd('FileType', {
  pattern = { 'text' },
  callback = function()
    vim.lsp.enable('triggerfish')
  end,
})
```

## Example

```
# In a .txt file, type:
@myfi

# Shows completions for all matching files in your project:
# - my_file.py
# - my_first.js
# - my_filter.ts
# - my_file.md
# - my_config.json
```

Note: The `@` trigger only works in `.txt` files. This allows you to reference any file in your project from text documents without triggering completions in your code files.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Check coverage
pytest --cov=src/triggerfish --cov-report=html

# Format code
black src/ tests/

# Type check
mypy src/

# Lint
ruff check src/ tests/
pylint src/
```

## Troubleshooting

- Logs location: `~/.triggerfish/logs/triggerfish.log`
- Make sure you're in a `.txt` file when testing `@` completions
- Check that the LSP client is configured with filetype `'text'`
- Verify the server is running by checking `:LspInfo` in Neovim

## License

Apache 2.0
