const vscode = require('vscode');
const { LanguageClient } = require('vscode-languageclient/node');

let client;

function activate(context) {
  const config = vscode.workspace.getConfiguration('triggerfish');
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  const defaultPythonPath = workspaceFolder
    ? `${workspaceFolder}/.venv/bin/python`
    : 'python';
  const pythonPath = config.get('pythonPath') || defaultPythonPath;

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
