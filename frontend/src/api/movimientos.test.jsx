import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const movimientosPath = path.join(__dirname, 'movimientos.js');

describe('T01 — listarMovimientos — RF-1', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('movimientos.js existe y usa request centralizado sin hardcodeo VITE_API_URL ni fetch directo', () => {
    expect(fs.existsSync(movimientosPath)).toBe(true);
    const content = fs.readFileSync(movimientosPath, 'utf8');
    expect(content).toMatch(/from\s+['"]\.\/client\.js['"]/);
    expect(content).toMatch(/request\(/);
    expect(content).not.toMatch(/VITE_API_URL/);
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).toMatch(/\/api\/v1\/movimientos/);
  });

  it('listarMovimientos hace GET /api/v1/movimientos y normaliza sin //', async () => {
    const { listarMovimientos } = await import('./movimientos.js');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [
        { id: 16, producto_codigo: 'PROD-003', proveedor_codigo: null, tipo: 'salida', cantidad: 8, motivo: 'Venta', fecha: '2026-09-08T12:00:00Z' },
        { id: 15, producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', tipo: 'entrada', cantidad: 10, motivo: 'Compra', fecha: '2026-09-08T11:00:00Z' },
      ],
      headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch);
    const data = await listarMovimientos();
    expect(data).toHaveLength(2);
    expect(data[0]).toHaveProperty('id');
    expect(data[0]).toHaveProperty('producto_codigo');
    expect(data[0]).toHaveProperty('proveedor_codigo');
    expect(data[0]).toHaveProperty('tipo');
    expect(data[0]).toHaveProperty('cantidad');
    expect(data[0]).toHaveProperty('motivo');
    expect(data[0]).toHaveProperty('fecha');
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/movimientos');
    expect(url).not.toContain('//api');
    expect(opts.method).toBe('GET');
  });

  it('listarMovimientos resuelve [] cuando API devuelve vacío', async () => {
    const { listarMovimientos } = await import('./movimientos.js');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' },
    }));
    const data = await listarMovimientos();
    expect(data).toEqual([]);
  });

  it('listarMovimientos no reordena frontend (orden fecha desc + id desc del backend)', async () => {
    const { listarMovimientos } = await import('./movimientos.js');
    const ordenado = [
      { id: 3, producto_codigo: 'PROD-001', proveedor_codigo: 'PROV-001', tipo: 'entrada', cantidad: 5, motivo: null, fecha: '2026-09-08T12:00:00Z' },
      { id: 2, producto_codigo: 'PROD-001', proveedor_codigo: null, tipo: 'salida', cantidad: 2, motivo: null, fecha: '2026-09-08T11:00:00Z' },
      { id: 1, producto_codigo: 'PROD-001', proveedor_codigo: null, tipo: 'entrada_inicial', cantidad: 10, motivo: null, fecha: '2026-09-07T10:00:00Z' },
    ];
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ordenado, headers: { get: () => 'application/json' } }));
    const data = await listarMovimientos();
    expect(data.map((m) => m.id)).toEqual([3, 2, 1]);
  });

  it('grep fetch vacío fuera de src/api — solo client.js y movimientos.js usan request', () => {
    const content = fs.readFileSync(movimientosPath, 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });
});

describe('T02 — crearEntrada / crearSalida — RF-2, RF-3', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('movimientos.js usa request sin hardcodeo VITE_API_URL ni fetch directo', () => {
    const content = fs.readFileSync(movimientosPath, 'utf8');
    expect(content).toMatch(/from\s+['"]\.\/client\.js['"]/);
    expect(content).toMatch(/request\(/);
    expect(content).not.toMatch(/VITE_API_URL/);
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).toMatch(/\/api\/v1\/movimientos\/entradas/);
    expect(content).toMatch(/\/api\/v1\/movimientos\/salidas/);
  });

  it('crearEntrada POST /entradas envía {producto_codigo,proveedor_codigo,cantidad,motivo?} (motivo ausente→omitido)', async () => {
    const { crearEntrada } = await import('./movimientos.js');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true, status: 201, json: async () => ({ id: 15, producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', tipo: 'entrada', cantidad: 10, motivo: 'Compra', fecha: '2026-09-08T11:00:00Z' }), headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch);
    // con motivo
    await crearEntrada({ producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', cantidad: 10, motivo: 'Compra' });
    let [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/movimientos/entradas');
    expect(opts.method).toBe('POST');
    expect(JSON.parse(opts.body)).toEqual({ producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', cantidad: 10, motivo: 'Compra' });
    // motivo ausente → omitido
    mockFetch.mockClear();
    await crearEntrada({ producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', cantidad: 5 });
    [, opts] = mockFetch.mock.calls[0];
    const bodyAusente = JSON.parse(opts.body);
    expect(bodyAusente).not.toHaveProperty('motivo');
    expect(bodyAusente).toEqual({ producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', cantidad: 5 });
    // motivo null → omitido (se envía sin motivo)
    mockFetch.mockClear();
    await crearEntrada({ producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', cantidad: 5, motivo: null });
    [, opts] = mockFetch.mock.calls[0];
    expect(JSON.parse(opts.body)).not.toHaveProperty('motivo');
    // motivo "" → omitido (no se envía vacío, backend lo validaría pero frontend lo omite)
    mockFetch.mockClear();
    await crearEntrada({ producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', cantidad: 5, motivo: '' });
    [, opts] = mockFetch.mock.calls[0];
    expect(JSON.parse(opts.body)).not.toHaveProperty('motivo');
  });

  it('crearSalida POST /salidas envía {producto_codigo,cantidad,motivo?} sin proveedor_codigo aunque se informe', async () => {
    const { crearSalida } = await import('./movimientos.js');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true, status: 201, json: async () => ({ id: 16, producto_codigo: 'PROD-003', tipo: 'salida', cantidad: 8, fecha: '2026-09-08T12:00:00Z' }), headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch);
    // sin proveedor
    await crearSalida({ producto_codigo: 'PROD-003', cantidad: 8, motivo: 'Venta' });
    let [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/movimientos/salidas');
    expect(opts.method).toBe('POST');
    expect(JSON.parse(opts.body)).toEqual({ producto_codigo: 'PROD-003', cantidad: 8, motivo: 'Venta' });
    // aunque se pase proveedor_codigo, se omite
    mockFetch.mockClear();
    await crearSalida({ producto_codigo: 'PROD-003', cantidad: 8, proveedor_codigo: 'PROV-002', motivo: 'Venta' });
    [, opts] = mockFetch.mock.calls[0];
    const body = JSON.parse(opts.body);
    expect(body).not.toHaveProperty('proveedor_codigo');
    expect(body).not.toHaveProperty('proveedor');
    // motivo ausente → omitido
    mockFetch.mockClear();
    await crearSalida({ producto_codigo: 'PROD-003', cantidad: 8 });
    [, opts] = mockFetch.mock.calls[0];
    expect(JSON.parse(opts.body)).not.toHaveProperty('motivo');
  });

  it('crearEntrada/crearSalida 422/404/400 mapean a validacion, 5xx/red a conexion', async () => {
    const { crearEntrada, crearSalida } = await import('./movimientos.js');
    // crearEntrada 422 cantidad inválida
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: 'Cantidad inválida' }), headers: { get: () => 'application/json' } }));
    await expect(crearEntrada({ producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', cantidad: 0 })).rejects.toMatchObject({ tipo: 'validacion', status: 422 });
    // crearEntrada 404 producto no existe
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({ detail: 'Producto no existe' }), headers: { get: () => 'application/json' } }));
    await expect(crearEntrada({ producto_codigo: 'NOPE', proveedor_codigo: 'PROV-002', cantidad: 5 })).rejects.toMatchObject({ tipo: 'validacion', status: 404 });
    // crearEntrada 400 inactivo
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Proveedor inactivo' }), headers: { get: () => 'application/json' } }));
    await expect(crearEntrada({ producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', cantidad: 5 })).rejects.toMatchObject({ tipo: 'validacion', status: 400 });
    // crearSalida 400 stock insuficiente
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Stock insuficiente' }), headers: { get: () => 'application/json' } }));
    await expect(crearSalida({ producto_codigo: 'PROD-003', cantidad: 100 })).rejects.toMatchObject({ tipo: 'validacion', status: 400 });
    // 5xx → conexion
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }));
    await expect(crearEntrada({ producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', cantidad: 5 })).rejects.toMatchObject({ tipo: 'conexion' });
    await expect(crearSalida({ producto_codigo: 'PROD-003', cantidad: 5 })).rejects.toMatchObject({ tipo: 'conexion' });
    // red
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    await expect(crearSalida({ producto_codigo: 'PROD-003', cantidad: 5 })).rejects.toMatchObject({ tipo: 'conexion' });
  });

  it('proveedor nunca se envía en salida aunque se informe con valor', async () => {
    const { crearSalida } = await import('./movimientos.js');
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({}), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', mockFetch);
    await crearSalida({ producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-999', proveedor: 'PROV-999', cantidad: 5, motivo: 'test' });
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body).not.toHaveProperty('proveedor_codigo');
    expect(body).not.toHaveProperty('proveedor');
    expect(body).not.toHaveProperty('proveedor_id');
  });
});

describe('T11 — Tests unidad src/api/movimientos.js (Vitest fetch mockeado) — RF-1..4', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('listar 200 con 7 campos, [] vacío, 401 validacion y 500 conexion, orden fecha desc', async () => {
    const { listarMovimientos } = await import('./movimientos.js');
    // 200 con 7 campos
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, status: 200, json: async () => [{ id: 1, producto_codigo: 'PROD-001', proveedor_codigo: 'PROV-001', tipo: 'entrada', cantidad: 10, motivo: 'Compra', fecha: '2026-09-08T11:00:00Z' }], headers: { get: () => 'application/json' },
    }));
    const data200 = await listarMovimientos();
    expect(data200[0]).toHaveProperty('id');
    expect(data200[0]).toHaveProperty('producto_codigo');
    expect(data200[0]).toHaveProperty('proveedor_codigo');
    expect(data200[0]).toHaveProperty('tipo');
    expect(data200[0]).toHaveProperty('cantidad');
    expect(data200[0]).toHaveProperty('motivo');
    expect(data200[0]).toHaveProperty('fecha');
    // [] vacío
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } }));
    const dataEmpty = await listarMovimientos();
    expect(dataEmpty).toEqual([]);
    // 401 → validacion sin Reintentar
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401, json: async () => ({ detail: 'No autorizado' }), headers: { get: () => 'application/json' } }));
    await expect(listarMovimientos()).rejects.toMatchObject({ tipo: 'validacion', status: 401 });
    // 500 → conexion con Reintentar
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }));
    await expect(listarMovimientos()).rejects.toMatchObject({ tipo: 'conexion', status: 500 });
    // orden fecha desc + id desc sin reordenar frontend
    const ordenado = [
      { id: 3, producto_codigo: 'PROD-001', proveedor_codigo: null, tipo: 'entrada', cantidad: 5, motivo: null, fecha: '2026-09-08T12:00:00Z' },
      { id: 2, producto_codigo: 'PROD-001', proveedor_codigo: null, tipo: 'salida', cantidad: 2, motivo: null, fecha: '2026-09-08T11:00:00Z' },
      { id: 1, producto_codigo: 'PROD-001', proveedor_codigo: null, tipo: 'entrada_inicial', cantidad: 10, motivo: null, fecha: '2026-09-07T10:00:00Z' },
    ];
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ordenado, headers: { get: () => 'application/json' } }));
    const dataOrden = await listarMovimientos();
    expect(dataOrden.map((m) => m.id)).toEqual([3, 2, 1]);
  });

  it('crearEntrada 201 con proveedor obligatorio, 404/400/422 mapean a validacion', async () => {
    const { crearEntrada } = await import('./movimientos.js');
    // 201
    const mock201 = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({ id: 15, producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', tipo: 'entrada', cantidad: 10, fecha: '2026-09-08T11:00:00Z' }), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', mock201);
    await crearEntrada({ producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', cantidad: 10, motivo: 'Compra' });
    expect(JSON.parse(mock201.mock.calls[0][1].body)).toHaveProperty('proveedor_codigo', 'PROV-002');
    expect(JSON.parse(mock201.mock.calls[0][1].body)).toHaveProperty('producto_codigo', 'PROD-003');
    // 404 producto/proveedor no existe
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({ detail: 'Producto no existe' }), headers: { get: () => 'application/json' } }));
    await expect(crearEntrada({ producto_codigo: 'NOPE', proveedor_codigo: 'PROV-002', cantidad: 5 })).rejects.toMatchObject({ tipo: 'validacion', status: 404 });
    // 400 inactivo
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Proveedor inactivo' }), headers: { get: () => 'application/json' } }));
    await expect(crearEntrada({ producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', cantidad: 5 })).rejects.toMatchObject({ tipo: 'validacion', status: 400 });
    // 422 cantidad/motivo
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: 'Cantidad inválida' }), headers: { get: () => 'application/json' } }));
    await expect(crearEntrada({ producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', cantidad: 0 })).rejects.toMatchObject({ tipo: 'validacion', status: 422 });
  });

  it('crearSalida 201, 400 stock insuficiente y 422 sin proveedor, nunca envía proveedor', async () => {
    const { crearSalida } = await import('./movimientos.js');
    // 201
    const mock201 = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({ id: 16, producto_codigo: 'PROD-003', tipo: 'salida', cantidad: 8, fecha: '2026-09-08T12:00:00Z' }), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', mock201);
    await crearSalida({ producto_codigo: 'PROD-003', cantidad: 8, motivo: 'Venta' });
    const body201 = JSON.parse(mock201.mock.calls[0][1].body);
    expect(body201).toEqual({ producto_codigo: 'PROD-003', cantidad: 8, motivo: 'Venta' });
    expect(body201).not.toHaveProperty('proveedor_codigo');
    // 400 stock insuficiente
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Stock insuficiente' }), headers: { get: () => 'application/json' } }));
    await expect(crearSalida({ producto_codigo: 'PROD-003', cantidad: 100 })).rejects.toMatchObject({ tipo: 'validacion', status: 400 });
    // 422 motivo/cantidad
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: 'Motivo inválido' }), headers: { get: () => 'application/json' } }));
    await expect(crearSalida({ producto_codigo: 'PROD-003', cantidad: 5, motivo: 'x' })).rejects.toMatchObject({ tipo: 'validacion', status: 422 });
    // nunca envía proveedor aunque se informe
    const mockNever = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({}), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', mockNever);
    await crearSalida({ producto_codigo: 'PROD-003', cantidad: 5, proveedor_codigo: 'PROV-999', motivo: 'test' });
    expect(JSON.parse(mockNever.mock.calls[0][1].body)).not.toHaveProperty('proveedor_codigo');
  });

  it('baja no existe en movimientos.js (append-only)', async () => {
    const content = fs.readFileSync(movimientosPath, 'utf8');
    expect(content).not.toMatch(/baja/i);
    expect(content).not.toMatch(/eliminar/i);
    expect(content).not.toMatch(/borrar/i);
    expect(content).not.toMatch(/delete/i);
    expect(content).not.toMatch(/remove/i);
    const mod = await import('./movimientos.js');
    expect(mod).not.toHaveProperty('bajaMovimiento');
    expect(mod).not.toHaveProperty('eliminarMovimiento');
    expect(mod).not.toHaveProperty('borrarMovimiento');
    expect(mod).not.toHaveProperty('deleteMovimiento');
    expect(typeof mod.listarMovimientos).toBe('function');
    expect(typeof mod.crearEntrada).toBe('function');
    expect(typeof mod.crearSalida).toBe('function');
  });

  it('verifica fetch solo en src/api y VITE_API_URL solo en client.js', () => {
    const apiDir = path.join(__dirname);
    const files = fs.readdirSync(apiDir).filter((f) => f.endsWith('.js'));
    let viteCount = 0;
    let fetchCount = 0;
    for (const f of files) {
      const content = fs.readFileSync(path.join(apiDir, f), 'utf8');
      if (content.includes('VITE_API_URL')) viteCount++;
      if (/fetch\s*\(/.test(content)) fetchCount++;
    }
    expect(viteCount).toBe(1);
    expect(fs.readFileSync(path.join(apiDir, 'client.js'), 'utf8')).toMatch(/VITE_API_URL/);
    expect(fetchCount).toBe(1);
    expect(fs.readFileSync(path.join(apiDir, 'client.js'), 'utf8')).toMatch(/fetch\s*\(/);
    expect(fs.readFileSync(movimientosPath, 'utf8')).not.toMatch(/VITE_API_URL/);
    expect(fs.readFileSync(movimientosPath, 'utf8')).not.toMatch(/fetch\s*\(/);
    // componentes/hooks/pages no deben tener fetch
    const srcRoot = path.join(__dirname, '..');
    const checkNoFetch = (dir) => {
      if (!fs.existsSync(dir)) return;
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const p = path.join(dir, entry.name);
        if (entry.isDirectory()) checkNoFetch(p);
        else if (entry.isFile() && (entry.name.endsWith('.jsx') || entry.name.endsWith('.js'))) {
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
