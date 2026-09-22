import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

describe('T02 — cliente Bearer e interceptor 401 — RF-4, RF-5', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
    vi.stubGlobal('fetch', vi.fn());
    vi.resetModules();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('inyecta Bearer en cada fetch excepto POST /auth/login', async () => {
    const { request, setAuthTokenGetter } = await import('./client.js');
    setAuthTokenGetter(() => 'jwt-test-token');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
      headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch);

    await request('/api/v1/productos', { method: 'GET' });
    expect(mockFetch.mock.calls[0][1].headers.Authorization).toBe('Bearer jwt-test-token');

    mockFetch.mockClear();
    await request('/api/v1/auth/login', { method: 'POST', body: JSON.stringify({ email: 'a@b.com', password: 'x' }) });
    const headersLogin = mockFetch.mock.calls[0][1].headers;
    expect(headersLogin.Authorization).toBeUndefined();
  });

  it('sin token no inyecta Authorization', async () => {
    const { request, setAuthTokenGetter } = await import('./client.js');
    setAuthTokenGetter(() => null);
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
      headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch);
    await request('/api/v1/stock', { method: 'GET' });
    expect(mockFetch.mock.calls[0][1].headers.Authorization).toBeUndefined();
  });

  it('401 en ruta protegida con token dispara onUnauthorized y lanza Sesión expirada', async () => {
    const { request, setAuthTokenGetter, setOnUnauthorized } = await import('./client.js');
    setAuthTokenGetter(() => 'jwt-test-token');
    const onUnauthorized = vi.fn();
    setOnUnauthorized(onUnauthorized);
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Not authenticated' }),
      headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch);
    await expect(request('/api/v1/productos', { method: 'GET' })).rejects.toMatchObject({
      status: 401,
      mensaje: expect.stringContaining('Sesión expirada'),
    });
    expect(onUnauthorized).toHaveBeenCalledTimes(1);
  });

  it('401 en POST /auth/login no dispara onUnauthorized', async () => {
    const { request, setAuthTokenGetter, setOnUnauthorized } = await import('./client.js');
    setAuthTokenGetter(() => 'jwt-test-token');
    const onUnauthorized = vi.fn();
    setOnUnauthorized(onUnauthorized);
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Credenciales inválidas' }),
      headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch);
    await expect(request('/api/v1/auth/login', { method: 'POST', body: JSON.stringify({}) })).rejects.toMatchObject({
      status: 401,
      mensaje: 'Credenciales inválidas',
    });
    expect(onUnauthorized).not.toHaveBeenCalled();
  });

  it('otros 4xx/5xx/red no disparan onUnauthorized', async () => {
    const { request, setAuthTokenGetter, setOnUnauthorized } = await import('./client.js');
    setAuthTokenGetter(() => 'jwt-test-token');
    const onUnauthorized = vi.fn();
    setOnUnauthorized(onUnauthorized);
    const mockFetch400 = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Error validacion' }),
      headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch400);
    await expect(request('/api/v1/productos', { method: 'GET' })).rejects.toMatchObject({ status: 400 });
    expect(onUnauthorized).not.toHaveBeenCalled();

    const mockFetch500 = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
      headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', mockFetch500);
    await expect(request('/api/v1/productos', { method: 'GET' })).rejects.toMatchObject({ status: 500 });
    expect(onUnauthorized).not.toHaveBeenCalled();
  });

  it('lógica vive solo en src/api/ (constitución §3)', async () => {
    const fs = await import('node:fs');
    const path = await import('node:path');
    const srcDir = path.resolve('src');
    const dirs = ['components', 'layout', 'pages', 'hooks', 'context'];
    for (const dir of dirs) {
      const full = path.join(srcDir, dir);
      if (!fs.existsSync(full)) continue;
      const files = fs.readdirSync(full).filter((f) => f.endsWith('.jsx') || f.endsWith('.js'));
      for (const f of files) {
        if (f.includes('.test.')) continue;
        const content = fs.readFileSync(path.join(full, f), 'utf8');
        // ningún componente debe hacer fetch directo ni manejar 401 global
        expect(content).not.toMatch(/fetch\s*\(/);
        // no debe contener lógica de interceptor fuera de api (excepto Login que muestra el mensaje)
        if (f !== 'AuthContext.jsx' && f !== 'Login.jsx') {
          expect(content).not.toMatch(/Sesión expirada/);
        }
      }
    }
  });
});
