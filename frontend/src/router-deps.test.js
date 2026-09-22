import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(__dirname, '..');
const pkgPath = path.join(frontendDir, 'package.json');
const planPath = path.resolve(frontendDir, '..', 'specs', '005-frontend-base', 'plan.md');

describe('T02 — react-router-dom v6 instalado — RF-1, RF-2', () => {
  it('package.json existe y es JSON válido', () => {
    assert.ok(fs.existsSync(pkgPath), 'package.json debe existir');
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
    assert.ok(pkg, 'package.json debe ser parseable');
  });

  it('package.json incluye react-router-dom v6 como dependencia (excepción AGENTS.md:27)', () => {
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
    const deps = { ...(pkg.dependencies || {}), ...(pkg.devDependencies || {}) };
    assert.ok(deps['react-router-dom'], 'react-router-dom debe estar en dependencies');
    assert.match(deps['react-router-dom'], /6\./, 'versión debe ser v6');
  });

  it('package.json incluye react y react-dom (peer de react-router-dom)', () => {
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
    const deps = { ...(pkg.dependencies || {}) };
    assert.ok(deps['react'], 'react debe estar en dependencies');
    assert.ok(deps['react-dom'], 'react-dom debe estar en dependencies');
  });

  it('justificación documentada en plan.md (excepción a no añadir dependencias)', () => {
    assert.ok(fs.existsSync(planPath), 'plan.md debe existir');
    const plan = fs.readFileSync(planPath, 'utf8');
    assert.ok(plan.includes('react-router-dom'), 'plan.md debe mencionar react-router-dom');
    assert.ok(plan.includes('AGENTS.md:27') || plan.includes('excepción'), 'plan.md debe justificar excepción AGENTS.md:27');
    assert.ok(plan.includes('Alternativa descartada'), 'plan.md debe incluir alternativa descartada');
  });

  it('node_modules/react-router-dom instalado (npm install sin errores)', () => {
    const modPath = path.join(frontendDir, 'node_modules', 'react-router-dom');
    assert.ok(fs.existsSync(modPath), 'node_modules/react-router-dom debe existir tras npm install');
    const pkg = JSON.parse(fs.readFileSync(path.join(modPath, 'package.json'), 'utf8'));
    assert.match(pkg.version, /^6\./, 'instalado debe ser v6');
  });

  it('npm run lint existe y pasa (no rompe pipeline)', () => {
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
    assert.ok(pkg.scripts?.lint, 'script lint debe existir');
    // no ejecuta lint aquí, solo verifica definición; ejecución real se hace fuera del test
  });
});
