import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const proveedoresPath = path.join(__dirname, 'proveedores.js');

describe('T02 — Fase 1 API proveedores — RF-2, RF-3, RF-4 — T01+T02', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('proveedores.js existe y usa request centralizado sin hardcodeo VITE_API_URL ni fetch directo', () => {
    expect(fs.existsSync(proveedoresPath)).toBe(true);
    const content = fs.readFileSync(proveedoresPath, 'utf8');
    expect(content).toMatch(/from\s+['"]\.\/client\.js['"]/);
    expect(content).toMatch(/request\(/);
    expect(content).not.toMatch(/VITE_API_URL/);
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).toMatch(/\/api\/v1\/proveedores/);
  });

  it('listarProveedores hace GET /api/v1/proveedores y normaliza sin //', async () => {
    const { listarProveedores } = await import('./proveedores.js');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: null, direccion: null }],
      headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch);
    const data = await listarProveedores();
    expect(data).toEqual([{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: null, direccion: null }]);
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/proveedores');
    expect(url).not.toContain('//api');
    expect(opts.method).toBe('GET');
  });

  it('listarProveedores resuelve [] cuando API devuelve vacío', async () => {
    const { listarProveedores } = await import('./proveedores.js');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' },
    }));
    const data = await listarProveedores();
    expect(data).toEqual([]);
  });

  it('crearProveedor POST envía {codigo,nombre,email?,telefono?,direccion?} ausente→omitido null→null', async () => {
    const { crearProveedor } = await import('./proveedores.js');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true, status: 201, json: async () => ({ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: null, direccion: null, estado: 'activo' }), headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch);

    // con todos los opcionales
    await crearProveedor({ codigo: 'PROV-001', nombre: 'Central', email: 'a@b.com', telefono: '+34 600', direccion: 'Calle 10' });
    let [, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe('POST');
    expect(JSON.parse(opts.body)).toEqual({ codigo: 'PROV-001', nombre: 'Central', email: 'a@b.com', telefono: '+34 600', direccion: 'Calle 10' });

    // opcionales ausentes → omitidos
    mockFetch.mockClear();
    await crearProveedor({ codigo: 'PROV-002', nombre: 'Norte' });
    [, opts] = mockFetch.mock.calls[0];
    const bodyAusente = JSON.parse(opts.body);
    expect(bodyAusente).toEqual({ codigo: 'PROV-002', nombre: 'Norte' });
    expect(bodyAusente).not.toHaveProperty('email');
    expect(bodyAusente).not.toHaveProperty('telefono');
    expect(bodyAusente).not.toHaveProperty('direccion');

    // null explícito → null
    mockFetch.mockClear();
    await crearProveedor({ codigo: 'PROV-003', nombre: 'Sur', email: null, telefono: null, direccion: null });
    [, opts] = mockFetch.mock.calls[0];
    const bodyNull = JSON.parse(opts.body);
    expect(bodyNull).toEqual({ codigo: 'PROV-003', nombre: 'Sur', email: null, telefono: null, direccion: null });

    // undefined → omitido igual que ausente
    mockFetch.mockClear();
    await crearProveedor({ codigo: 'PROV-004', nombre: 'Este', email: undefined });
    [, opts] = mockFetch.mock.calls[0];
    expect(JSON.parse(opts.body)).not.toHaveProperty('email');
  });

  it('crearProveedor 409/400/422 mapean a validacion, 5xx/red a conexion', async () => {
    const { crearProveedor } = await import('./proveedores.js');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ detail: 'Código ya existe' }), headers: { get: () => 'application/json' } }));
    await expect(crearProveedor({ codigo: 'DUPE', nombre: 'X' })).rejects.toMatchObject({ tipo: 'validacion', status: 409 });

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: 'Email inválido' }), headers: { get: () => 'application/json' } }));
    await expect(crearProveedor({ codigo: 'X', nombre: 'Y', email: 'bad' })).rejects.toMatchObject({ tipo: 'validacion', status: 422 });

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Bad request' }), headers: { get: () => 'application/json' } }));
    await expect(crearProveedor({ codigo: 'X', nombre: 'Y' })).rejects.toMatchObject({ tipo: 'validacion' });

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }));
    await expect(crearProveedor({ codigo: 'X', nombre: 'Y' })).rejects.toMatchObject({ tipo: 'conexion' });

    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    await expect(crearProveedor({ codigo: 'X', nombre: 'Y' })).rejects.toMatchObject({ tipo: 'conexion' });
  });

  it('editarProveedor PATCH solo {nombre,email,telefono,direccion} — null borra, ausente conserva, "" nunca enviado, sin codigo/estado', async () => {
    const { editarProveedor } = await import('./proveedores.js');
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ codigo: 'PROV-001', nombre: 'Nuevo', email: null }), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', mockFetch);

    // editar nombre + borrar email con null
    await editarProveedor('PROV-001', { nombre: 'Nuevo', email: null });
    let [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/proveedores/PROV-001');
    expect(opts.method).toBe('PATCH');
    let body = JSON.parse(opts.body);
    expect(body).toEqual({ nombre: 'Nuevo', email: null });
    expect(body).not.toHaveProperty('codigo');
    expect(body).not.toHaveProperty('estado');

    // ausente conserva → no se envía
    mockFetch.mockClear();
    await editarProveedor('PROV-001', { nombre: 'Solo Nombre' });
    [, opts] = mockFetch.mock.calls[0];
    body = JSON.parse(opts.body);
    expect(body).toEqual({ nombre: 'Solo Nombre' });
    expect(body).not.toHaveProperty('email');

    // "" nunca se envía → se omite (bloqueo local, no llega a API)
    mockFetch.mockClear();
    await editarProveedor('PROV-001', { nombre: 'Nuevo', email: '' });
    [, opts] = mockFetch.mock.calls[0];
    body = JSON.parse(opts.body);
    expect(body).toEqual({ nombre: 'Nuevo' });
    expect(body).not.toHaveProperty('email');

    // "   " también omitido
    mockFetch.mockClear();
    await editarProveedor('PROV-001', { email: '   ', telefono: '+34 600' });
    [, opts] = mockFetch.mock.calls[0];
    body = JSON.parse(opts.body);
    expect(body).toEqual({ telefono: '+34 600' });

    // undefined ausente no se envía
    mockFetch.mockClear();
    await editarProveedor('PROV-001', { nombre: 'X', telefono: undefined });
    [, opts] = mockFetch.mock.calls[0];
    body = JSON.parse(opts.body);
    expect(body).toEqual({ nombre: 'X' });
  });

  it('editarProveedor 404/400/422 mapean a validacion, 5xx/red a conexion', async () => {
    const { editarProveedor } = await import('./proveedores.js');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({ detail: 'No encontrado' }), headers: { get: () => 'application/json' } }));
    await expect(editarProveedor('NOPE', { nombre: 'X' })).rejects.toMatchObject({ tipo: 'validacion', status: 404 });

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Ya inactivo' }), headers: { get: () => 'application/json' } }));
    await expect(editarProveedor('PROV-001', { nombre: 'X' })).rejects.toMatchObject({ tipo: 'validacion' });

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }));
    await expect(editarProveedor('PROV-001', { nombre: 'X' })).rejects.toMatchObject({ tipo: 'conexion' });
  });

  it('bajaProveedor DELETE /{codigo} y 400 ya inactivo → validacion, 5xx→conexion, codifica codigo', async () => {
    const { bajaProveedor } = await import('./proveedores.js');
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ codigo: 'PROV-001', estado: 'inactivo' }), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', mockFetch);
    await bajaProveedor('PROV-001');
    let [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/proveedores/PROV-001');
    expect(opts.method).toBe('DELETE');

    // encodeURIComponent
    mockFetch.mockClear();
    await bajaProveedor('PROV 001');
    [url] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/api/v1/proveedores/PROV%20001');

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Ya dado de baja' }), headers: { get: () => 'application/json' } }));
    await expect(bajaProveedor('PROV-001')).rejects.toMatchObject({ tipo: 'validacion' });

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({ detail: 'No encontrado' }), headers: { get: () => 'application/json' } }));
    await expect(bajaProveedor('NOPE')).rejects.toMatchObject({ tipo: 'validacion', status: 404 });

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }));
    await expect(bajaProveedor('PROV-001')).rejects.toMatchObject({ tipo: 'conexion' });
  });

  it('grep fetch vacío fuera de src/api — solo client.js y proveedores.js usan request', () => {
    const content = fs.readFileSync(proveedoresPath, 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });
});

describe('T13 — Tests unidad proveedores.js — RF-1..5 — cobertura completa', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('listar 200 ordenado por codigo sin reordenar frontend, [] , 404→validacion, 500→conexion', async () => {
    const { listarProveedores } = await import('./proveedores.js');
    // ordenado por codigo: frontend no reordena, devuelve tal cual
    const ordenado = [
      { codigo: 'PROV-001', nombre: 'A', email: null, telefono: null, direccion: null },
      { codigo: 'PROV-002', nombre: 'B', email: null, telefono: null, direccion: null },
      { codigo: 'PROV-010', nombre: 'C', email: null, telefono: null, direccion: null },
    ];
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ordenado, headers: { get: () => 'application/json' } }));
    const data = await listarProveedores();
    expect(data.map((p) => p.codigo)).toEqual(['PROV-001', 'PROV-002', 'PROV-010']);
    // 404
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({ detail: 'No encontrado' }), headers: { get: () => 'application/json' } }));
    await expect(listarProveedores()).rejects.toMatchObject({ tipo: 'validacion', status: 404 });
    // 500
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }));
    await expect(listarProveedores()).rejects.toMatchObject({ tipo: 'conexion' });
  });

  it('crear 201/409/422 con email/telefono null/ausente/"" y 500→conexion', async () => {
    const { crearProveedor } = await import('./proveedores.js');
    // 201
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({ codigo: 'PROV-001', nombre: 'X', estado: 'activo' }), headers: { get: () => 'application/json' } }));
    await expect(crearProveedor({ codigo: 'PROV-001', nombre: 'X' })).resolves.toBeDefined();
    // 409
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ detail: 'Código ya existe' }), headers: { get: () => 'application/json' } }));
    await expect(crearProveedor({ codigo: 'PROV-001', nombre: 'X' })).rejects.toMatchObject({ tipo: 'validacion', status: 409 });
    // 422 con "" (email vacío debe mapearse a validacion, frontend envía "" y backend rechaza)
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url, opts) => {
      const body = JSON.parse(opts.body);
      if (body.email === '') return { ok: false, status: 422, json: async () => ({ detail: 'Email inválido' }), headers: { get: () => 'application/json' } };
      return { ok: false, status: 422, json: async () => ({ detail: 'Error' }), headers: { get: () => 'application/json' } };
    }));
    await expect(crearProveedor({ codigo: 'PROV-002', nombre: 'Y', email: '' })).rejects.toMatchObject({ tipo: 'validacion', status: 422 });
    // null y ausente ya cubiertos en T02, verificamos que "" se envía y no se omite
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({}), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', mockFetch);
    await crearProveedor({ codigo: 'PROV-003', nombre: 'Z', email: '' });
    expect(JSON.parse(mockFetch.mock.calls[0][1].body)).toHaveProperty('email', '');
  });

  it('editar PATCH null borra / ausente conserva / "" nunca enviado / payload vacío → validacion', async () => {
    const { editarProveedor } = await import('./proveedores.js');
    const mockFetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', mockFetch);
    // null borra
    await editarProveedor('PROV-001', { email: null });
    expect(JSON.parse(mockFetch.mock.calls[0][1].body)).toEqual({ email: null });
    // ausente conserva
    mockFetch.mockClear();
    await editarProveedor('PROV-001', { nombre: 'Nuevo' });
    expect(JSON.parse(mockFetch.mock.calls[0][1].body)).not.toHaveProperty('email');
    // "" nunca enviado
    mockFetch.mockClear();
    await editarProveedor('PROV-001', { email: '' });
    expect(JSON.parse(mockFetch.mock.calls[0][1].body)).not.toHaveProperty('email');
    // payload vacío {} → backend 422 validacion (simulado)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: 'Payload vacío' }), headers: { get: () => 'application/json' } }));
    await expect(editarProveedor('PROV-001', {})).rejects.toMatchObject({ tipo: 'validacion', status: 422 });
  });

  it('baja DELETE 200/404/400/500 mapeo correcto', async () => {
    const { bajaProveedor } = await import('./proveedores.js');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ codigo: 'PROV-001', estado: 'inactivo' }), headers: { get: () => 'application/json' } }));
    await expect(bajaProveedor('PROV-001')).resolves.toBeDefined();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Ya dado de baja' }), headers: { get: () => 'application/json' } }));
    await expect(bajaProveedor('PROV-001')).rejects.toMatchObject({ tipo: 'validacion', status: 400 });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }));
    await expect(bajaProveedor('PROV-001')).rejects.toMatchObject({ tipo: 'conexion' });
  });

  it('verifica fetch solo en src/api/ y VITE_API_URL solo en client.js', () => {
    const srcDir = path.resolve(__dirname, '..');
    const apiDir = path.join(srcDir, 'api');
    const clientContent = fs.readFileSync(path.join(apiDir, 'client.js'), 'utf8');
    expect(clientContent).toMatch(/VITE_API_URL/);
    expect(clientContent).toMatch(/fetch\s*\(/);
    // proveedores.js no debe tener VITE_API_URL ni fetch
    const provContent = fs.readFileSync(path.join(apiDir, 'proveedores.js'), 'utf8');
    expect(provContent).not.toMatch(/VITE_API_URL/);
    expect(provContent).not.toMatch(/fetch\s*\(/);
    // ningún componente/hook/page debe tener fetch
    for (const sub of ['components', 'hooks', 'pages']) {
      const dir = path.join(srcDir, sub);
      if (!fs.existsSync(dir)) continue;
      for (const f of fs.readdirSync(dir)) {
        if (f.endsWith('.test.jsx') || f.endsWith('.test.js')) continue;
        const c = fs.readFileSync(path.join(dir, f), 'utf8');
        expect(c).not.toMatch(/fetch\s*\(/);
      }
    }
    // solo client.js debe leer VITE_API_URL en src/api
    for (const f of fs.readdirSync(apiDir)) {
      if (f === 'client.js') continue;
      if (f.endsWith('.test.jsx')) continue;
      const c = fs.readFileSync(path.join(apiDir, f), 'utf8');
      expect(c).not.toMatch(/VITE_API_URL/);
    }
  });
});
