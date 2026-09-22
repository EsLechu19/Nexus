import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const productosPath = path.join(__dirname, 'productos.js');

describe('T01 — listarProductos — RF-1', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it('productos.js existe y usa request centralizado sin hardcodeo VITE_API_URL', () => {
    expect(fs.existsSync(productosPath)).toBe(true);
    const content = fs.readFileSync(productosPath, 'utf8');
    expect(content).toMatch(/from\s+['"]\.\/client\.js['"]/);
    expect(content).toMatch(/request\(/);
    expect(content).not.toMatch(/http:\/\/localhost/);
    expect(content).not.toMatch(/VITE_API_URL/); // solo client.js debe leer env
    expect(content).toMatch(/\/api\/v1\/productos/);
  });

  it('listarProductos hace GET /api/v1/productos y normaliza sin //', async () => {
    const { listarProductos } = await import('./productos.js');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [{ sku: 'PS5-001', nombre: 'Play', categoria: 'consola', stock_inicial: 10 }],
      headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch);
    const data = await listarProductos();
    expect(data).toEqual([{ sku: 'PS5-001', nombre: 'Play', categoria: 'consola', stock_inicial: 10 }]);
    const [url] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/productos');
    expect(url).not.toMatch(/\/\//.source.replace('//','')); // no doble barra después de dominio
  });

  it('listarProductos resuelve [] cuando API devuelve vacío', async () => {
    const { listarProductos } = await import('./productos.js');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' },
    }));
    const data = await listarProductos();
    expect(data).toEqual([]);
  });

  it('solo src/api contiene fetch (constitución §3)', () => {
    const content = fs.readFileSync(productosPath, 'utf8');
    expect(content).toMatch(/request\(/);
    // productos.js no debe hacer fetch directo
    expect(content).not.toMatch(/fetch\s*\(/);
  });
});

describe('T02 — crear/editar/baja — RF-2, RF-3, RF-4', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it('crearProducto POST envía {nombre,sku,categoria,stock_inicial?} (vacío→ausencia)', async () => {
    const { crearProducto } = await import('./productos.js');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true, status: 201, json: async () => ({ sku: 'X', nombre: 'Y', categoria: 'videojuego', stock_inicial: 0, estado: 'activo' }), headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch);
    // con stock
    await crearProducto({ nombre: 'Y', sku: 'X', categoria: 'videojuego', stock_inicial: 10 });
    let [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/productos');
    expect(opts.method).toBe('POST');
    expect(JSON.parse(opts.body)).toEqual({ nombre: 'Y', sku: 'X', categoria: 'videojuego', stock_inicial: 10 });
    // stock vacío → ausencia (no enviar campo)
    mockFetch.mockClear();
    await crearProducto({ nombre: 'Y', sku: 'X', categoria: 'videojuego', stock_inicial: undefined });
    [, opts] = mockFetch.mock.calls[0];
    expect(JSON.parse(opts.body)).not.toHaveProperty('stock_inicial');
    // stock null → ausencia
    mockFetch.mockClear();
    await crearProducto({ nombre: 'Y', sku: 'X', categoria: 'videojuego', stock_inicial: null });
    [, opts] = mockFetch.mock.calls[0];
    expect(JSON.parse(opts.body)).not.toHaveProperty('stock_inicial');
  });

  it('crearProducto 409/400 mapean a validacion, 5xx/red a conexion', async () => {
    const { crearProducto } = await import('./productos.js');
    // 409 duplicado
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ detail: 'SKU ya existe' }), headers: { get: () => 'application/json' } }));
    await expect(crearProducto({ nombre: 'Y', sku: 'DUPE', categoria: 'videojuego' })).rejects.toMatchObject({ tipo: 'validacion', status: 409 });
    // 500 → conexion
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }));
    await expect(crearProducto({ nombre: 'Y', sku: 'X', categoria: 'videojuego' })).rejects.toMatchObject({ tipo: 'conexion' });
  });

  it('editarProducto PATCH solo {nombre,categoria} sin sku/stock', async () => {
    const { editarProducto } = await import('./productos.js');
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ sku: 'PS5-001', nombre: 'Nuevo', categoria: 'consola', stock_inicial: 10 }), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', mockFetch);
    await editarProducto('PS5-001', { nombre: 'Nuevo', categoria: 'consola' });
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/productos/PS5-001');
    expect(opts.method).toBe('PATCH');
    const body = JSON.parse(opts.body);
    expect(body).toEqual({ nombre: 'Nuevo', categoria: 'consola' });
    expect(body).not.toHaveProperty('sku');
    expect(body).not.toHaveProperty('stock_inicial');
  });

  it('editarProducto 404/400 inmutable mapean a validacion', async () => {
    const { editarProducto } = await import('./productos.js');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({ detail: 'No encontrado' }), headers: { get: () => 'application/json' } }));
    await expect(editarProducto('NOPE', { nombre: 'X' })).rejects.toMatchObject({ tipo: 'validacion', status: 404 });
  });

  it('bajaProducto DELETE /{sku} y 400 ya inactivo → validacion', async () => {
    const { bajaProducto } = await import('./productos.js');
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ sku: 'PS5-001', estado: 'inactivo' }), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', mockFetch);
    await bajaProducto('PS5-001');
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/productos/PS5-001');
    expect(opts.method).toBe('DELETE');
    // ya inactivo → validacion
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Ya dado de baja' }), headers: { get: () => 'application/json' } }));
    await expect(bajaProducto('PS5-001')).rejects.toMatchObject({ tipo: 'validacion' });
  });

  it('sin hardcodeo VITE_API_URL en productos.js', () => {
    const content = fs.readFileSync(productosPath, 'utf8');
    expect(content).not.toMatch(/VITE_API_URL/);
  });
});
