const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const rootDir = path.resolve(__dirname, '..');
const isWin = process.platform === 'win32';

// Detecta o executavel python do ambiente virtual local se existir
const venvPython = isWin
  ? path.join(rootDir, '.venv', 'Scripts', 'python.exe')
  : path.join(rootDir, '.venv', 'bin', 'python');

const pythonBin = fs.existsSync(venvPython) ? venvPython : (isWin ? 'python' : 'python3');
const args = process.argv.slice(2);

const res = spawnSync(pythonBin, args, { stdio: 'inherit', cwd: rootDir });
process.exit(res.status ?? 0);
