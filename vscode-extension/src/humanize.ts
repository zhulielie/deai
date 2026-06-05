import * as vscode from 'vscode';
import { spawn } from 'child_process';

const PROVIDER_DEFAULTS: Record<string, { base_url: string; model: string }> = {
  openai: { base_url: '', model: 'gpt-4o-mini' },
  deepseek: { base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  anthropic: { base_url: 'https://api.anthropic.com/v1', model: 'claude-3-5-sonnet-20241022' },
  groq: { base_url: 'https://api.groq.com/openai/v1', model: 'llama-3.2-90b-vision-preview' },
  together: { base_url: 'https://api.together.xyz/v1', model: 'meta-llama/Llama-3.2-70B-Instruct-Turbo' },
  ollama: { base_url: 'http://localhost:11434/v1', model: 'llama3.2' },
  custom: { base_url: '', model: '' },
};

export function humanizeCode(source: string): Promise<string> {
  const config = vscode.workspace.getConfiguration('deai');
  const engine = config.get<string>('engine', 'ast');
  const style = config.get<string>('style', 'random');

  return new Promise((resolve, reject) => {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    const cwd = workspaceFolder ? workspaceFolder.uri.fsPath : process.cwd();

    const script = buildPythonScript(source, engine, style, config);

    const python = spawn('python', ['-c', script], {
      cwd,
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    python.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(stderr || 'Python exited with code ' + code));
        return;
      }
      try {
        const result = JSON.parse(stdout.trim());
        if (result.error) {
          reject(new Error(result.error));
        } else {
          resolve(result.output);
        }
      } catch {
        resolve(stdout.trim());
      }
    });

    python.on('error', (err) => {
      reject(new Error('Failed to run Python: ' + err.message + '. Make sure deai is installed: pip install deai'));
    });
  });
}

function buildPythonScript(source: string, engine: string, style: string, config: vscode.WorkspaceConfiguration): string {
  const escapedSource = JSON.stringify(source);
  const seed = Math.floor(Math.random() * 1000000);
  const projectRoot = process.cwd().replace(/\\/g, '\\\\');

  if (engine === 'ai') {
    const provider = config.get<string>('provider', 'openai');
    const apiKey = config.get<string>('apiKey', '');
    const baseUrl = config.get<string>('baseUrl', '');
    const model = config.get<string>('model', '');
    const preset = PROVIDER_DEFAULTS[provider] || PROVIDER_DEFAULTS.custom;
    const finalBaseUrl = baseUrl || preset.base_url;
    const finalModel = model || preset.model;

    const lines = [
      'import json, random, sys',
      "sys.path.insert(0, r'" + projectRoot + "')",
      'from deai.ai_humanizer import humanize_with_ai',
      'from deai.styles import STYLES, pick_style',
      '',
      'source = ' + escapedSource,
      'style_name = ' + JSON.stringify(style),
      'seed = ' + seed,
      'rng = random.Random(seed)',
      "style = pick_style(rng) if style_name == 'random' or style_name not in STYLES else STYLES[style_name]",
      '',
      'try:',
      '    result = humanize_with_ai(',
      '        source, style,',
      '        api_key=' + (apiKey ? JSON.stringify(apiKey) : 'None') + ',',
      '        base_url=' + (finalBaseUrl ? JSON.stringify(finalBaseUrl) : 'None') + ',',
      '        model=' + (finalModel ? JSON.stringify(finalModel) : 'None') + ',',
      '        provider=' + JSON.stringify(provider),
      '    )',
      '    print(json.dumps({"output": result}))',
      'except Exception as e:',
      '    print(json.dumps({"error": str(e)}))',
    ];
    return lines.join('\n');
  }

  const lines = [
    'import json, random, sys',
    "sys.path.insert(0, r'" + projectRoot + "')",
    'from deai.languages.python import humanize_python',
    'from deai.styles import STYLES, pick_style',
    '',
    'source = ' + escapedSource,
    'style_name = ' + JSON.stringify(style),
    'seed = ' + seed,
    'rng = random.Random(seed)',
    "style = pick_style(rng) if style_name == 'random' or style_name not in STYLES else STYLES[style_name]",
    '',
    'try:',
    '    result = humanize_python(source, style, seed)',
    '    print(json.dumps({"output": result}))',
    'except Exception as e:',
    '    print(json.dumps({"error": str(e)}))',
  ];
  return lines.join('\n');
}
