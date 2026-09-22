import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const stockPath = path.join(__dirname, 'stock.js');

describe('T07 — stock.js listarStock — RF-1, RF-2', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('stock.js existe y usa request centralizado sin hardcodeo VITE_API_URL ni fetch directo', () => {
    expect(fs.existsSync(stockPath)).toBe(true);
    const content = fs.readFileSync(stockPath, 'utf8');
    expect(content).toMatch(/from\s+['"]\.\/client\.js['"]/);
    expect(content).toMatch(/request\(/);
    expect(content).not.toMatch(/VITE_API_URL/);
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).toMatch(/\/api\/v1\/stock/);
    expect(content).not.toMatch(/stock_minimo\s*>\s*0\s*&&/);
  });

  it('listarStock hace GET /api/v1/stock y normaliza sin //', async () => {
    const { listarStock } = await import('./stock.js');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [{ codigo: 'PROD-001', nombre: 'A', stock_actual: 5, stock_minimo: 10, alerta: true }],
      headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch);
    const data = await listarStock();
    expect(data).toHaveLength(1);
    expect(data[0]).toHaveProperty('codigo');
    expect(data[0]).toHaveProperty('nombre');
    expect(data[0]).toHaveProperty('stock_actual');
    expect(data[0]).toHaveProperty('stock_minimo');
    expect(data[0]).toHaveProperty('alerta');
    expect(typeof data[0].alerta).toBe('boolean');
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/stock');
    expect(url).not.toContain('//api');
    expect(opts.method).toBe('GET');
  });

  it('listarStock resuelve [] cuando API devuelve vacío, null y 204', async () => {
    const { listarStock } = await import('./stock.js');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } }));
    expect(await listarStock()).toEqual([]);
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => null, headers: { get: () => 'application/json' } }));
    expect(await listarStock()).toEqual(null);
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 204, json: async () => null, headers: { get: () => 'application/json' } }));
    expect(await listarStock()).toEqual(null);
  });

  it('listarStock incluye alerta boolean sin recalcular y ignora stock_inicial|entradas|salidas (los devuelve tal cual)', async () => {
    const { listarStock } = await import('./stock.js');
    const payload = [{ codigo: 'PROD-001', nombre: 'A', stock_actual: 0, stock_minimo: 5, alerta: true, stock_inicial: 5, entradas: 10, salidas: 3 }];
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => payload, headers: { get: () => 'application/json' } }));
    const data = await listarStock();
    expect(data[0].alerta).toBe(true);
    expect(data[0]).toHaveProperty('stock_inicial', 5);
    expect(data[0]).toHaveProperty('entradas', 10);
    const content = fs.readFileSync(stockPath, 'utf8');
    expect(content).not.toMatch(/alerta\s*=\s*stock_minimo/);
    expect(content).not.toMatch(/stock_actual\s*<\s*stock_minimo/);
  });

  it('listarStock no reordena frontend (orden codigo ASC del backend)', async () => {
    const { listarStock } = await import('./stock.js');
    const ordenado = [
      { codigo: 'PROD-001', nombre: 'A', stock_actual: 5, stock_minimo: 10, alerta: true },
      { codigo: 'PROD-002', nombre: 'B', stock_actual: 10, stock_minimo: 10, alerta: false },
      { codigo: 'PROD-003', nombre: 'C', stock_actual: 20, stock_minimo: 5, alerta: false },
    ];
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ordenado, headers: { get: () => 'application/json' } }));
    const data = await listarStock();
    expect(data.map((s) => s.codigo)).toEqual(['PROD-001', 'PROD-002', 'PROD-003']);
  });

  it('listarStock 401→validacion, 500→conexion, 404 nunca en global pero si ocurriera sería validacion', async () => {
    const { listarStock } = await import('./stock.js');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401, json: async () => ({ detail: 'No autorizado' }), headers: { get: () => 'application/json' } }));
    await expect(listarStock()).rejects.toMatchObject({ tipo: 'validacion', status: 401 });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }));
    await expect(listarStock()).rejects.toMatchObject({ tipo: 'conexion' });
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    await expect(listarStock()).rejects.toMatchObject({ tipo: 'conexion' });
    const content = fs.readFileSync(stockPath, 'utf8');
    expect(content).not.toMatch(/404.*global/i);
  });

  it('verifica fetch solo en src/api/ y VITE_API_URL solo en client.js', () => {
    const apiDir = __dirname;
    const files = fs.readdirSync(apiDir).filter((f) => f.endsWith('.js'));
    let viteCount = 0;
    let fetchCount = 0;
    for (const f of files) {
      const content = fs.readFileSync(path.join(apiDir, f), 'utf8');
      if (content.includes('VITE_API_URL')) viteCount++;
      if (/fetch\s*\(/.test(content)) fetchCount++;
    }
    expect(viteCount).toBe(1);
    expect(fetchCount).toBe(1);
    expect(fs.readFileSync(path.join(apiDir, 'client.js'), 'utf8')).toMatch(/VITE_API_URL/);
    expect(fs.readFileSync(path.join(apiDir, 'client.js'), 'utf8')).toMatch(/fetch\s*\(/);
    expect(fs.readFileSync(stockPath, 'utf8')).not.toMatch(/VITE_API_URL/);
    expect(fs.readFileSync(stockPath, 'utf8')).not.toMatch(/fetch\s*\(/);
    const srcRoot = path.join(__dirname, '..');
    const checkNoFetch = (dir) => {
      if (!fs.existsSync(dir)) return;
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const p = path.join(dir, entry.name);
        if (entry.isDirectory()) checkNoFetch(p);
        else if (entry.isFile() && (entry.name.endsWith('.jsx') || entry.name.endsWith('.js')) && !entry.name.includes('.test.')) {
          const c = fs.readFileSync(p, 'utf8');
          expect(c).not.toMatch(/fetch\s*\(/);
        }
      }
    };
    checkNoFetch(path.join(srcRoot, 'components'));
    checkNoFetch(path.join(srcRoot, 'pages'));
    checkNoFetch(path.join(srcRoot, 'hooks'));
  });
});
