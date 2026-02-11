# Triggerfish LSP

Lightning-fast LSP server with smart trigger-based completions for files, classes, and functions.

## Features

- **`@` trigger** for file completions with fuzzy search
- **`.` trigger** for class completions with fuzzy search
- **`#` trigger** for method/function completions with fuzzy search
- Works in `.txt` files by default
- Automatic workspace indexing with `universal-ctags` integration
- Shows all project files and code symbols
- Intelligent directory filtering (ignores `.git`, `node_modules`, etc.)

## Requirements

- Python 3.9+
- `universal-ctags` (for class/method/function parsing)
  - macOS: `brew install universal-ctags`
  - Ubuntu/Debian: `apt install universal-ctags`
  - Arch: `pacman -S ctags`
  - Windows: Download from [ctags.io](https://ctags.io/)

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

### VSCode

1. Install a generic LSP client extension like [vscode-lsp-client](https://marketplace.visualstudio.com/items?itemName=vscode-lsp-client)

2. Add to your `settings.json`:

```json
{
  "lsp.languages": {
    "plaintext": {
      "command": "python",
      "args": ["-m", "triggerfish"],
      "filetypes": ["plaintext", "txt"],
      "triggerCharacters": ["@", ".", "#"]
    }
  }
}
```

Or create a custom extension:

3. Create `.vscode/extensions/triggerfish/package.json`:

```json
{
  "name": "triggerfish-lsp",
  "displayName": "Triggerfish LSP",
  "version": "0.1.0",
  "engines": { "vscode": "^1.75.0" },
  "activationEvents": ["onLanguage:plaintext"],
  "main": "./extension.js",
  "contributes": {
    "configuration": {
      "title": "Triggerfish",
      "properties": {
        "triggerfish.pythonPath": {
          "type": "string",
          "default": "python",
          "description": "Path to Python executable"
        }
      }
    }
  }
}
```

4. Create `.vscode/extensions/triggerfish/extension.js`:

```javascript
const vscode = require('vscode');
const { LanguageClient } = require('vscode-languageclient/node');

let client;

function activate(context) {
  const config = vscode.workspace.getConfiguration('triggerfish');
  const pythonPath = config.get('pythonPath') || 'python';

  const serverOptions = {
    command: pythonPath,
    args: ['-m', 'triggerfish']
  };

  const clientOptions = {
    documentSelector: [{ scheme: 'file', language: 'plaintext' }],
    synchronize: {
      fileEvents: vscode.workspace.createFileSystemWatcher('**/*')
    }
  };

  client = new LanguageClient(
    'triggerfish',
    'Triggerfish LSP',
    serverOptions,
    clientOptions
  );

  client.start();
}

function deactivate() {
  if (client) return client.stop();
}

module.exports = { activate, deactivate };
```

### Neovim

#### Modern Setup (Neovim 0.10+)

Add to your `init.lua`:

```lua
-- Triggerfish LSP setup using vim.lsp.config
vim.lsp.config.triggerfish = {
  cmd = { 'python3', '-m', 'triggerfish' },
  filetypes = { 'text', 'txt' },
  root_markers = { '.git', '.hg', '.svn' },
  settings = {},
}

-- Enable for text files
vim.api.nvim_create_autocmd('FileType', {
  pattern = { 'text', 'txt' },
  callback = function(args)
    vim.lsp.enable('triggerfish', args.buf)
  end,
})
```

#### Using nvim-lspconfig

```lua
local lspconfig = require('lspconfig')
local configs = require('lspconfig.configs')

-- Register triggerfish if not already registered
if not configs.triggerfish then
  configs.triggerfish = {
    default_config = {
      cmd = { 'python3', '-m', 'triggerfish' },
      filetypes = { 'text', 'txt' },
      root_dir = lspconfig.util.root_pattern('.git', '.hg', '.svn'),
      settings = {},
    },
  }
end

-- Setup triggerfish
lspconfig.triggerfish.setup({
  on_attach = function(client, bufnr)
    -- Optional: Add custom keymaps
    local opts = { buffer = bufnr, noremap = true, silent = true }
    vim.keymap.set('i', '@', '@', opts)  -- Trigger file completion
    vim.keymap.set('i', '.', '.', opts)  -- Trigger class completion
    vim.keymap.set('i', '#', '#', opts)  -- Trigger method completion
  end,
})
```

#### Lazy.nvim Plugin Manager

```lua
{
  'neovim/nvim-lspconfig',
  config = function()
    local lspconfig = require('lspconfig')
    local configs = require('lspconfig.configs')

    if not configs.triggerfish then
      configs.triggerfish = {
        default_config = {
          cmd = { 'python3', '-m', 'triggerfish' },
          filetypes = { 'text', 'txt' },
          root_dir = lspconfig.util.root_pattern('.git'),
          settings = {},
        },
      }
    end

    lspconfig.triggerfish.setup({})
  end,
}
```

### Zed

1. Create or edit `~/.config/zed/settings.json`:

```json
{
  "lsp": {
    "triggerfish": {
      "binary": {
        "path": "python3",
        "arguments": ["-m", "triggerfish"]
      },
      "settings": {},
      "initialization_options": {}
    }
  },
  "languages": {
    "Plain Text": {
      "language_servers": ["triggerfish"],
      "format_on_save": "off",
      "tab_size": 2
    }
  }
}
```

2. Create `~/.config/zed/languages/text.json` (optional):

```json
{
  "name": "Plain Text",
  "path_suffixes": ["txt"],
  "line_comments": [],
  "language_servers": ["triggerfish"]
}
```

### Generic LSP Client

For any LSP client:

- **Command:** `python3 -m triggerfish`
- **Trigger characters:** `@`, `.`, `#`
- **Filetypes:** `text`, `txt`, `plaintext`
- **Root markers:** `.git`, `.hg`, `.svn`

## Examples

### File Completions with `@`

In a `.txt` file, type:
```
@myfi
```

Shows completions for all matching files in your project:
- `my_file.py`
- `my_first.js`
- `my_filter.ts`
- `my_file.md`
- `my_config.json`

### Class Completions with `.`

In a `.txt` file, type:
```
.UserAuth
```

Shows completions for all matching classes:
- `UserAuthentication`
- `UserAuthProvider`
- `UserAuthManager`

### Method/Function Completions with `#`

In a `.txt` file, type:
```
#get_user
```

Shows completions for all matching methods and functions:
- `get_user_by_id`
- `get_user_profile`
- `get_user_settings`

### Real-World Usage

```txt
Notes.txt:

TODO: Check the implementation in @src/auth/login.py
The .UserAuthentication class handles this
Call #validate_credentials to verify the user

Bug in @components/Button.tsx
The .Button class needs updating
Fix #handleClick method
```

**Note:** All triggers (`.`, `#`, `@`) currently only work in `.txt` files. This allows you to reference files, classes, and functions from text documents without triggering completions in your code files.

## Configuration

Triggerfish can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `TRIGGERFISH_LOG_FILE` | `~/.triggerfish/logs/triggerfish.log` | Log file location |
| `TRIGGERFISH_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `TRIGGERFISH_CTAGS_EXECUTABLE` | `ctags` | Path to ctags executable |
| `TRIGGERFISH_CTAGS_TIMEOUT` | `30` | Timeout for ctags execution (seconds) |
| `TRIGGERFISH_MIN_FUZZY_SCORE` | `60` | Minimum fuzzy match score (0-100) |
| `TRIGGERFISH_MAX_COMPLETION_ITEMS` | `50` | Maximum completion items to return |

### Examples

```bash
# Use custom ctags
export TRIGGERFISH_CTAGS_EXECUTABLE=/usr/local/bin/ctags

# Increase timeout for large files
export TRIGGERFISH_CTAGS_TIMEOUT=60

# Show more completions
export TRIGGERFISH_MAX_COMPLETION_ITEMS=100

# More lenient fuzzy matching
export TRIGGERFISH_MIN_FUZZY_SCORE=40

# Debug logging
export TRIGGERFISH_LOG_LEVEL=DEBUG

# Start server with custom config
python -m triggerfish
```

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

### No completions appearing

- **Logs location:** `~/.triggerfish/logs/triggerfish.log`
- Make sure you're in a `.txt` file when testing completions
- Check that the LSP client is configured with filetype `'text'` or `'txt'`
- Verify the server is running:
  - Neovim: Check `:LspInfo`
  - VSCode: Check "Output" panel → "Triggerfish LSP"
  - Zed: Check debug panel

### Class/Method completions not working

- Ensure `universal-ctags` is installed: `ctags --version`
- Check if ctags is in your PATH: `which ctags` (Unix) or `where ctags` (Windows)
- Look for ctags errors in the log file
- Some files may not be parseable by ctags (check language support)

### Completions showing wrong symbols

- The workspace index is built on LSP initialization
- Restart the LSP server to rebuild the index:
  - Neovim: `:LspRestart triggerfish`
  - VSCode: Reload window (Cmd/Ctrl+R)
  - Zed: Restart editor

### Performance issues

- Check log file for ctags timeout errors
- Large projects may take longer to index initially
- Increase ctags timeout: `export TRIGGERFISH_CTAGS_TIMEOUT=60`

### Testing the server

```bash
# Check if ctags is working
ctags --version

# Test ctags on a file
ctags --output-format=json --fields=* --excmd=pattern your_file.py

# Start server with debug logging
python -m triggerfish --log-level DEBUG

# Check logs
tail -f ~/.triggerfish/logs/triggerfish.log
```

## License

Apache 2.0
