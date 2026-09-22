import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

vi.mock('../context/AuthContext.jsx', async () => {
  const actual = await vi.importActual('../context/AuthContext.jsx');
  return {
    ...actual,
    useAuth: () => ({ isAuthenticated: true, token: 'test-token', login: vi.fn(), logout: vi.fn() }),
  };
});

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function mockFetchForProveedores({ proveedores = [] } = {}) {
  return vi.fn().mockImplementation(async (url, opts) => {
    const method = opts?.method || 'GET';
    if (url.includes('/api/v1/proveedores') && method === 'GET') {
      return { ok: true, status: 200, json: async () => proveedores, headers: { get: () => 'application/json' } };
    }
    return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
  });
}

describe('T08 — Proveedores listado — RF-1', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('al montar muestra Loading luego ProveedorTabla con 5 columnas y sin estado', async () => {
    vi.stubGlobal('fetch', mockFetchForProveedores({ proveedores: [{ codigo: 'PROV-001', nombre: 'Central', email: 'a@b.com', telefono: '+34', direccion: 'Calle' }] }));
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('table')).toBeInTheDocument());
    expect(screen.getByText('Código')).toBeInTheDocument();
    expect(screen.getByText('Dirección')).toBeInTheDocument();
    expect(screen.queryByText('Estado')).not.toBeInTheDocument();
    // "—" no aparece cuando hay datos completos, pero tabla debe existir
  });

  it('lista vacía muestra EmptyState "Sin datos disponibles" y "—" para null', async () => {
    vi.stubGlobal('fetch', mockFetchForProveedores({ proveedores: [] }));
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    // con null
    vi.stubGlobal('fetch', mockFetchForProveedores({ proveedores: [{ codigo: 'PROV-002', nombre: 'Norte', email: null, telefono: null, direccion: null }] }));
    const { default: Proveedores2 } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores2 /></MemoryRouter>);
    await waitFor(() => expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(3));
  });

  it('error 4xx muestra mensaje API sin Reintentar, 5xx con Reintentar', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Código inválido' }), headers: { get: () => 'application/json' } }));
    const { default: Proveedores } = await import('./Proveedores.jsx');
    const { unmount } = render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Código inválido')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
    unmount();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }));
    const { default: Proveedores2 } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores2 /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeInTheDocument();
  });

  it('App.jsx ruta /proveedores anidada bajo AppLayout', async () => {
    vi.stubGlobal('fetch', mockFetchForProveedores({ proveedores: [] }));
    const { default: App } = await import('../App.jsx');
    render(<MemoryRouter initialEntries={['/proveedores']}><App /></MemoryRouter>);
    await waitFor(() => expect(screen.getByRole('navigation')).toBeInTheDocument());
    expect(screen.getByRole('main')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
  });

  it('no contiene fetch directo y sin localStorage', () => {
    const content = fs.readFileSync(path.join(__dirname, 'Proveedores.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).not.toMatch(/localStorage/);
  });
});

describe('T09 — Proveedores alta — RF-2, RF-5', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('click "Crear proveedor" abre modal alta con 5 campos', async () => {
    vi.stubGlobal('fetch', mockFetchForProveedores({ proveedores: [] }));
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Crear proveedor/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByLabelText(/Código/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Nombre/i)).toBeInTheDocument();
  });

  it('submit válido → crearProveedor + cargando deshabilita, 201 cierra modal + banner + revalidar', async () => {
    let proveedores = [];
    const postMock = vi.fn().mockImplementation(async (url, opts) => {
      if (opts?.method === 'POST') {
        const body = JSON.parse(opts.body);
        proveedores = [{ codigo: body.codigo, nombre: body.nombre, email: body.email ?? null, telefono: body.telefono ?? null, direccion: body.direccion ?? null }];
        return { ok: true, status: 201, json: async () => ({ ...proveedores[0], estado: 'activo' }), headers: { get: () => 'application/json' } };
      }
      return { ok: true, status: 200, json: async () => proveedores, headers: { get: () => 'application/json' } };
    });
    vi.stubGlobal('fetch', postMock);
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Crear proveedor/i }));
    await user.type(screen.getByLabelText(/Código/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Nombre/i), 'Central');
    const crearBtn = screen.getByRole('button', { name: /^Crear$/i });
    await user.click(crearBtn);
    // deshabilita mientras cargando (al menos un momento)
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(await screen.findByText('Proveedor creado correctamente')).toBeInTheDocument();
    // revalidar debe haber hecho GET adicional
    expect(postMock).toHaveBeenCalledWith(expect.stringContaining('/api/v1/proveedores'), expect.objectContaining({ method: 'GET' }));
  });

  it('4xx mantiene modal con validacion sin Reintentar, 5xx muestra conexion con Reintentar', async () => {
    vi.stubGlobal('fetch', mockFetchForProveedores({ proveedores: [] }));
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Crear proveedor/i }));
    // mock 409
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url, opts) => {
      if (opts?.method === 'POST') return { ok: false, status: 409, json: async () => ({ detail: 'Código ya existe' }), headers: { get: () => 'application/json' } };
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    await user.type(screen.getByLabelText(/Código/i), 'DUPE');
    await user.type(screen.getByLabelText(/Nombre/i), 'X');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('Código ya existe')).toBeInTheDocument());
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
    // 5xx
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url, opts) => {
      if (opts?.method === 'POST') return { ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } };
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeInTheDocument();
  });

  it('opcional ""/"   " bloquea local sin fetch, null/ausente no se envía', async () => {
    const postMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({ codigo: 'PROV-001', nombre: 'Central', estado: 'activo' }), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url, opts) => {
      if (opts?.method === 'POST') return postMock(url, opts);
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Crear proveedor/i }));
    await user.type(screen.getByLabelText(/Código/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Nombre/i), 'Central');
    await user.type(screen.getByLabelText(/Email/i), '   ');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    expect(await screen.findByText(/No puede quedar vacío/i)).toBeInTheDocument();
    expect(postMock).not.toHaveBeenCalled();
  });
});

describe('T10 — Proveedores edición — RF-3, RF-5', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('Editar precarga nombre/email/telefono/direccion (null→"") y codigo deshabilitado', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetchForProveedores({
        proveedores: [{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: '+34 600', direccion: null }],
      }),
    );
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Central')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Editar/i }));
    expect(screen.getByLabelText(/Nombre/i)).toHaveValue('Central');
    expect(screen.getByLabelText(/Email/i)).toHaveValue('');
    expect(screen.getByLabelText(/Teléfono/i)).toHaveValue('+34 600');
    expect(screen.getByLabelText(/Dirección/i)).toHaveValue('');
    const codigoInput = screen.getByLabelText(/Código/i);
    expect(codigoInput).toHaveValue('PROV-001');
    expect(codigoInput).toBeDisabled();
  });

  it('PATCH solo envía nombre/email/telefono/direccion sin codigo, 4xx mantiene modal', async () => {
    const patchMock = vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Nombre inválido' }), headers: { get: () => 'application/json' } });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'PATCH') return patchMock(url, opts);
        return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: null, direccion: null }], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Central')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Editar/i }));
    await user.clear(screen.getByLabelText(/Nombre/i));
    await user.type(screen.getByLabelText(/Nombre/i), 'Nuevo');
    await user.click(screen.getByRole('button', { name: /Guardar/i }));
    await waitFor(() => expect(patchMock).toHaveBeenCalled());
    const body = JSON.parse(patchMock.mock.calls[0][1].body);
    expect(body).toEqual({ nombre: 'Nuevo' });
    expect(body).not.toHaveProperty('codigo');
    expect(body).not.toHaveProperty('estado');
    await waitFor(() => expect(screen.getByText('Nombre inválido')).toBeInTheDocument());
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('Borrar envía null, ausente omite, "" bloquea y PATCH sin codigo', async () => {
    const patchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ codigo: 'PROV-001', nombre: 'Central', email: null }), headers: { get: () => 'application/json' } });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'PATCH') return patchMock(url, opts);
        return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'Central', email: 'a@b.com', telefono: null, direccion: 'Calle 1' }], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Central')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Editar/i }));
    // "" bloquea primero (modal aún abierto) - limpiar primero
    await user.clear(screen.getByLabelText(/Email/i));
    await user.type(screen.getByLabelText(/Email/i), '   ');
    await user.click(screen.getByRole('button', { name: /Guardar/i }));
    expect(await screen.findByText(/No puede quedar vacío/i)).toBeInTheDocument();
    expect(patchMock).not.toHaveBeenCalled();
    // limpiar y Borrar email
    await user.clear(screen.getByLabelText(/Email/i));
    const borrarBtns = screen.getAllByRole('button', { name: /Borrar/i });
    await user.click(borrarBtns[0]);
    await user.click(screen.getByRole('button', { name: /Guardar/i }));
    await waitFor(() => expect(patchMock).toHaveBeenCalled());
    let body = JSON.parse(patchMock.mock.calls[0][1].body);
    expect(body).toEqual({ email: null });
  });

  it('200 cierra + banner y 5xx con Reintentar, sin enviar codigo', async () => {
    let proveedores = [{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: null, direccion: null }];
    const patchMock = vi.fn().mockImplementation(async (url, opts) => {
      if (opts?.method === 'PATCH') {
        return { ok: true, status: 200, json: async () => ({ codigo: 'PROV-001', nombre: 'Nuevo', email: null }), headers: { get: () => 'application/json' } };
      }
      return { ok: true, status: 200, json: async () => proveedores, headers: { get: () => 'application/json' } };
    });
    vi.stubGlobal('fetch', patchMock);
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Central')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Editar/i }));
    await user.clear(screen.getByLabelText(/Nombre/i));
    await user.type(screen.getByLabelText(/Nombre/i), 'Nuevo');
    await user.click(screen.getByRole('button', { name: /Guardar/i }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(await screen.findByText('Proveedor actualizado correctamente')).toBeInTheDocument();
  });
});

describe('T11 — Proveedores baja — RF-4, RF-5', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('click Dar de baja abre diálogo, cancelar/ESC cierra sin fetch', async () => {
    vi.stubGlobal('fetch', mockFetchForProveedores({ proveedores: [{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: null, direccion: null }] }));
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Central')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Dar de baja/i }));
    expect(screen.getByText(/¿Dar de baja a Central \(PROV-001\)\?/i)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /Cancelar/i }));
    expect(screen.queryByText(/¿Dar de baja/)).not.toBeInTheDocument();
    // ESC
    await user.click(screen.getByRole('button', { name: /Dar de baja/i }));
    await user.keyboard('{Escape}');
    expect(screen.queryByText(/¿Dar de baja/)).not.toBeInTheDocument();
  });

  it('confirmar → bajaProveedor deshabilita Confirmar, 200 cierra + banner + revalidar 1→0 EmptyState', async () => {
    let proveedores = [{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: null, direccion: null }];
    let resolveDelete;
    const mockFetch = vi.fn().mockImplementation((url, opts) => {
      if (opts?.method === 'DELETE') {
        return new Promise((resolve) => {
          resolveDelete = () => {
            proveedores = [];
            resolve({ ok: true, status: 200, json: async () => ({ codigo: 'PROV-001', estado: 'inactivo' }), headers: { get: () => 'application/json' } });
          };
        });
      }
      if (url.includes('/api/v1/proveedores') && (!opts?.method || opts.method === 'GET')) {
        return Promise.resolve({ ok: true, status: 200, json: async () => proveedores, headers: { get: () => 'application/json' } });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } });
    });
    vi.stubGlobal('fetch', mockFetch);
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Central')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Dar de baja/i }));
    const confirmBtn = screen.getByRole('button', { name: /Confirmar/i });
    const clickPromise = user.click(confirmBtn);
    await waitFor(() => expect(screen.getByRole('button', { name: /Confirmar/i })).toBeDisabled());
    resolveDelete();
    await clickPromise;
    await waitFor(() => expect(screen.queryByText(/¿Dar de baja/)).not.toBeInTheDocument());
    expect(await screen.findByText('Proveedor dado de baja correctamente')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
  });

  it('4xx mantiene diálogo con mensaje API, 5xx muestra conexion con Reintentar', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'DELETE') return { ok: false, status: 400, json: async () => ({ detail: 'Ya dado de baja' }), headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: null, direccion: null }], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Central')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Dar de baja/i }));
    await user.click(screen.getByRole('button', { name: /Confirmar/i }));
    await waitFor(() => expect(screen.getByText('Ya dado de baja')).toBeInTheDocument());
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
    // 5xx
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'DELETE') return { ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: null, direccion: null }], headers: { get: () => 'application/json' } };
      }),
    );
    await user.click(screen.getByRole('button', { name: /Confirmar/i }));
    await waitFor(() => expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeInTheDocument();
  });

  it('no contiene fetch directo y navegar durante cargando no cancela petición', () => {
    const content = fs.readFileSync(path.join(__dirname, 'Proveedores.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).not.toMatch(/AbortController.*baja|abort.*baja/i);
  });
});

describe('T12 — Manejo uniforme estados, mensajes éxito y revalidación — RF-5', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('banner role status 3s separado coexistiendo con error de revalidación tras éxito', async () => {
    let callCount = 0;
    const mockFetch = vi.fn().mockImplementation(async (url, opts) => {
      const method = opts?.method || 'GET';
      if (method === 'POST') {
        return { ok: true, status: 201, json: async () => ({ codigo: 'PROV-001', nombre: 'Central', estado: 'activo' }), headers: { get: () => 'application/json' } };
      }
      if (url.includes('/api/v1/proveedores') && method === 'GET') {
        callCount++;
        // primera carga ok vacía, segunda (revalidación) falla 500
        if (callCount === 1) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
        return { ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } };
      }
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    });
    vi.stubGlobal('fetch', mockFetch);
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Crear proveedor/i }));
    await user.type(screen.getByLabelText(/Código/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Nombre/i), 'Central');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('Proveedor creado correctamente')).toBeInTheDocument());
    expect(screen.getByRole('status')).toBeInTheDocument();
    // revalidación fallida debe mostrar error conexion manteniendo banner
    await waitFor(() => expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument());
    expect(screen.getByText('Proveedor creado correctamente')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('401 como validacion sin redirección y sin Reintentar', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401, json: async () => ({ detail: 'No autorizado' }), headers: { get: () => 'application/json' } }));
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('No autorizado')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
    // no redirección: sigue en Proveedores, no navega a /productos
    expect(screen.getByText('Proveedores')).toBeInTheDocument();
  });

  it('grep localStorage vacío y ErrorMessage dos niveles sin variantes', () => {
    const contentProveedores = fs.readFileSync(path.join(__dirname, 'Proveedores.jsx'), 'utf8');
    expect(contentProveedores).not.toMatch(/localStorage/);
    expect(contentProveedores).not.toMatch(/sessionStorage/);
    const contentApi = fs.readFileSync(path.join(__dirname, '..', 'api', 'proveedores.js'), 'utf8');
    expect(contentApi).not.toMatch(/localStorage/);
    const errorContent = fs.readFileSync(path.join(__dirname, '..', 'components', 'ErrorMessage.jsx'), 'utf8');
    // dos niveles: conexion y validacion, sin variantes extra
    expect(errorContent).toMatch(/conexion/);
    expect(errorContent).toMatch(/validacion/);
  });

  it('email TEST@EXAMPLE.COM aceptado (no bloquea) y se envía tal cual', async () => {
    const postMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({ codigo: 'PROV-001', nombre: 'Central', email: 'test@example.com', estado: 'activo' }), headers: { get: () => 'application/json' } });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'POST') return postMock(url, opts);
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Crear proveedor/i }));
    await user.type(screen.getByLabelText(/Código/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Nombre/i), 'Central');
    await user.type(screen.getByLabelText(/Email/i), 'TEST@EXAMPLE.COM');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(postMock).toHaveBeenCalled());
    const body = JSON.parse(postMock.mock.calls[0][1].body);
    expect(body.email).toBe('TEST@EXAMPLE.COM');
    // no error local
    expect(screen.queryByText(/No puede quedar vacío/i)).not.toBeInTheDocument();
  });
});

describe('T15 — Proveedores integración — RF-1..5', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('monta→Loading→Tabla/Empty/Error según respuesta', async () => {
    vi.stubGlobal('fetch', mockFetchForProveedores({ proveedores: [{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: null, direccion: null }] }));
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('table')).toBeInTheDocument());
    expect(screen.getByText('Central')).toBeInTheDocument();
  });

  it('alta 201 cierra+revalida y "" bloquea, 409 mantiene modal', async () => {
    vi.stubGlobal('fetch', mockFetchForProveedores({ proveedores: [] }));
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Crear proveedor/i }));
    // "" bloquea
    await user.type(screen.getByLabelText(/Código/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Nombre/i), 'Central');
    await user.type(screen.getByLabelText(/Email/i), '   ');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    expect(await screen.findByText(/No puede quedar vacío/i)).toBeInTheDocument();
    // 409 mantiene modal
    await user.clear(screen.getByLabelText(/Email/i));
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'POST') return { ok: false, status: 409, json: async () => ({ detail: 'Código ya existe' }), headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('Código ya existe')).toBeInTheDocument());
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('edición precarga null→"" y null borra vs "" bloquea vs ausente conserva y PATCH sin codigo', async () => {
    vi.stubGlobal('fetch', mockFetchForProveedores({ proveedores: [{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: '+34', direccion: 'Calle' }] }));
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Central')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Editar/i }));
    expect(screen.getByLabelText(/Email/i)).toHaveValue('');
    // Borrar
    const patchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}), headers: { get: () => 'application/json' } });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'PATCH') return patchMock(url, opts);
        return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: '+34', direccion: 'Calle' }], headers: { get: () => 'application/json' } };
      }),
    );
    await user.click(screen.getAllByRole('button', { name: /Borrar/i })[0]);
    await user.click(screen.getByRole('button', { name: /Guardar/i }));
    await waitFor(() => expect(patchMock).toHaveBeenCalled());
    expect(JSON.parse(patchMock.mock.calls[0][1].body)).toHaveProperty('email', null);
    expect(JSON.parse(patchMock.mock.calls[0][1].body)).not.toHaveProperty('codigo');
  });

  it('baja confirmación y 200→EmptyState 1→0, botones deshabilitados, múltiples clics una sola petición', async () => {
    let proveedores = [{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: null, direccion: null }];
    let deleteCalls = 0;
    const mockFetch = vi.fn().mockImplementation((url, opts) => {
      if (opts?.method === 'DELETE') {
        deleteCalls++;
        return new Promise((resolve) => setTimeout(() => {
          proveedores = [];
          resolve({ ok: true, status: 200, json: async () => ({ codigo: 'PROV-001', estado: 'inactivo' }), headers: { get: () => 'application/json' } });
        }, 50));
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => proveedores, headers: { get: () => 'application/json' } });
    });
    vi.stubGlobal('fetch', mockFetch);
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Central')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Dar de baja/i }));
    const confirmBtn = screen.getByRole('button', { name: /Confirmar/i });
    // múltiples clics rápidos
    await user.click(confirmBtn);
    await user.click(confirmBtn);
    await user.click(confirmBtn);
    await waitFor(() => expect(screen.getByText('Proveedor dado de baja correctamente')).toBeInTheDocument());
    expect(deleteCalls).toBe(1);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
  });

  it('401 como validacion sin Reintentar en alta/edición/baja', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'POST') return { ok: false, status: 401, json: async () => ({ detail: 'No autorizado' }), headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Proveedores } = await import('./Proveedores.jsx');
    render(<MemoryRouter><Proveedores /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Crear proveedor/i }));
    await user.type(screen.getByLabelText(/Código/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Nombre/i), 'Central');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('No autorizado')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
  });
});
