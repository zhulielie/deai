"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const humanize_1 = require("./humanize");
function activate(context) {
    const humanizeSelection = vscode.commands.registerCommand('deai.humanizeSelection', async () => {
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
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'deai: Humanizing selection...',
            cancellable: false,
        }, async () => {
            try {
                const result = await (0, humanize_1.humanizeCode)(text);
                editor.edit((editBuilder) => {
                    editBuilder.replace(selection, result);
                });
                vscode.window.showInformationMessage('✅ Selection humanized');
            }
            catch (err) {
                vscode.window.showErrorMessage(`deai error: ${err.message}`);
            }
        });
    });
    const humanizeFile = vscode.commands.registerCommand('deai.humanizeFile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }
        const document = editor.document;
        const text = document.getText();
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'deai: Humanizing file...',
            cancellable: false,
        }, async () => {
            try {
                const result = await (0, humanize_1.humanizeCode)(text);
                const fullRange = new vscode.Range(document.positionAt(0), document.positionAt(text.length));
                editor.edit((editBuilder) => {
                    editBuilder.replace(fullRange, result);
                });
                vscode.window.showInformationMessage('✅ File humanized');
            }
            catch (err) {
                vscode.window.showErrorMessage(`deai error: ${err.message}`);
            }
        });
    });
    const openWebUI = vscode.commands.registerCommand('deai.openWebUI', () => {
        vscode.env.openExternal(vscode.Uri.parse('http://localhost:5000'));
    });
    context.subscriptions.push(humanizeSelection, humanizeFile, openWebUI);
}
function deactivate() { }
//# sourceMappingURL=extension.js.map