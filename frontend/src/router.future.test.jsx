import { describe, it, expect } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('Buenas prácticas — React Router future flags — RF-1', () => {
  it('main.jsx BrowserRouter opta a v7_startTransition y v7_relativeSplatPath', () => {
    const content = fs.readFileSync(path.join(__dirname, 'main.jsx'), 'utf8');
    expect(content).toMatch(/future/);
    expect(content).toMatch(/v7_startTransition/);
    expect(content).toMatch(/v7_relativeSplatPath/);
  });

  it('no deja warnings de deprecations en código (se usa future flag)', () => {
    const main = fs.readFileSync(path.join(__dirname, 'main.jsx'), 'utf8');
    // debe contener future con ambos flags en true
    expect(main).toMatch(/v7_startTransition:\s*true/);
    expect(main).toMatch(/v7_relativeSplatPath:\s*true/);
  });
});
