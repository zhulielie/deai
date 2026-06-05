import * as vscode from 'vscode';
import { humanizeCode } from './humanize';

export function activate(context: vscode.ExtensionContext) {
  const humanizeSelection = vscode.commands.registerCommand(
    'deai.humanizeSelection',
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
      }

      const selection = editor.selection;
      const text = editor.document.getText(selection);
      if (!text.trim()) {
        vscode.window.showWarningMessage('No code selected');
        return;
      }

      await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: 'deai: Humanizing selection...',
          cancellable: false,
        },
        async () => {
          try {
            const result = await humanizeCode(text);
            editor.edit((editBuilder) => {
              editBuilder.replace(selection, result);
            });
            vscode.window.showInformationMessage('✅ Selection humanized');
          } catch (err: any) {
            vscode.window.showErrorMessage(`deai error: ${err.message}`);
          }
        }
      );
    }
  );

  const humanizeFile = vscode.commands.registerCommand(
    'deai.humanizeFile',
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
      }

      const document = editor.document;
      const text = document.getText();

      await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: 'deai: Humanizing file...',
          cancellable: false,
        },
        async () => {
          try {
            const result = await humanizeCode(text);
            const fullRange = new vscode.Range(
              document.positionAt(0),
              document.positionAt(text.length)
            );
            editor.edit((editBuilder) => {
              editBuilder.replace(fullRange, result);
            });
            vscode.window.showInformationMessage('✅ File humanized');
          } catch (err: any) {
            vscode.window.showErrorMessage(`deai error: ${err.message}`);
          }
        }
      );
    }
  );

  const openWebUI = vscode.commands.registerCommand('deai.openWebUI', () => {
    vscode.env.openExternal(vscode.Uri.parse('http://localhost:5000'));
  });

  context.subscriptions.push(humanizeSelection, humanizeFile, openWebUI);
}

export function deactivate() {}
