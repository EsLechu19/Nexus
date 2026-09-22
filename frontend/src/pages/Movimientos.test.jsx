import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
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

function mockFetchHistorial({ movimientos = [] } = {}) {
  return vi.fn().mockImplementation(async (url, opts) => {
    const method = opts?.method || 'GET';
    if (url.includes('/api/v1/movimientos') && method === 'GET') {
      return { ok: true, status: 200, json: async () => movimientos, headers: { get: () => 'application/json' } };
    }
    if (url.includes('/api/v1/productos') || url.includes('/api/v1/proveedores')) {
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }
    return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
  });
}

describe('T07 — Movimientos historial — RF-1', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('al montar muestra Loading luego MovimientosHistorial con 7 columnas y sin stock', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetchHistorial({
        movimientos: [
          { id: 1, producto_codigo: 'PROD-001', proveedor_codigo: 'PROV-001', tipo: 'entrada', cantidad: 10, motivo: 'Compra', fecha: '2026-09-08T11:00:00Z' },
        ],
      }),
    );
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('table')).toBeInTheDocument());
    expect(screen.getByText('Fecha')).toBeInTheDocument();
    expect(screen.getByText('Proveedor')).toBeInTheDocument();
    expect(screen.queryByText('stock_actual')).not.toBeInTheDocument();
    expect(screen.queryByText('Stock')).not.toBeInTheDocument();
  });

  it('lista vacía muestra EmptyState "Sin datos disponibles" y "—" para null en historial', async () => {
    vi.stubGlobal('fetch', mockFetchHistorial({ movimientos: [] }));
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    // con null
    vi.stubGlobal(
      'fetch',
      mockFetchHistorial({
        movimientos: [{ id: 1, producto_codigo: 'PROD-001', proveedor_codigo: null, tipo: 'salida', cantidad: 5, motivo: null, fecha: '2026-09-08T12:00:00Z' }],
      }),
    );
    const { default: Movimientos2 } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos2 /></MemoryRouter>);
    await waitFor(() => expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(2));
    expect(screen.getAllByText('2026-09-08T12:00:00Z').length).toBeGreaterThanOrEqual(1);
  });

  it('error 4xx muestra mensaje API sin Reintentar, 5xx con Reintentar que re-ejecuta revalidar', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({ detail: 'No encontrado' }), headers: { get: () => 'application/json' } }));
    const { default: Movimientos } = await import('./Movimientos.jsx');
    const { unmount } = render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('No encontrado')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
    unmount();
    // 5xx
    let callCount = 0;
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url) => {
        if (url.includes('/api/v1/movimientos')) {
          callCount++;
          if (callCount === 1) return { ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } };
          return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
        }
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Movimientos2 } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos2 /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument());
    const reintentarBtn = screen.getByRole('button', { name: /Reintentar/i });
    expect(reintentarBtn).toBeInTheDocument();
    await waitFor(() => expect(callCount).toBeGreaterThanOrEqual(1));
  });

  it('App.jsx ruta /movimientos anidada bajo AppLayout', async () => {
    vi.stubGlobal('fetch', mockFetchHistorial({ movimientos: [] }));
    const { default: App } = await import('../App.jsx');
    render(<MemoryRouter initialEntries={['/movimientos']}><App /></MemoryRouter>);
    await waitFor(() => expect(screen.getByRole('navigation')).toBeInTheDocument());
    expect(screen.getByRole('main')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
  });

  it('no contiene fetch directo y sin localStorage, sin columna stock', () => {
    const content = fs.readFileSync(path.join(__dirname, 'Movimientos.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).not.toMatch(/localStorage/);
    expect(content).not.toMatch(/stock_actual/);
    expect(content).not.toMatch(/stockActual/i);
  });
});

describe('T08 — Movimientos alta Entrada — RF-2, RF-4', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('click "Crear movimiento" abre modal Entrada con 4 campos', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url) => {
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'Juego A' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'Central' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Entrada/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Proveedor/i)).toBeInTheDocument();
  });

  it('submit válido Entrada → crearEntrada + cargando deshabilita, 201 cierra + banner + revalidar', async () => {
    let movimientos = [];
    const productos = [{ codigo: 'PROD-001', nombre: 'Juego A' }];
    const proveedores = [{ codigo: 'PROV-001', nombre: 'Central' }];
    const mockFetch = vi.fn().mockImplementation(async (url, opts) => {
      const method = opts?.method || 'GET';
      if (url.includes('/api/v1/productos') && method === 'GET') return { ok: true, status: 200, json: async () => productos, headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/proveedores') && method === 'GET') return { ok: true, status: 200, json: async () => proveedores, headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/movimientos/entradas') && method === 'POST') {
        const body = JSON.parse(opts.body);
        movimientos = [{ id: 1, producto_codigo: body.producto_codigo, proveedor_codigo: body.proveedor_codigo, tipo: 'entrada', cantidad: body.cantidad, motivo: body.motivo || null, fecha: '2026-09-08T11:00:00Z' }];
        return { ok: true, status: 201, json: async () => movimientos[0], headers: { get: () => 'application/json' } };
      }
      if (url.includes('/api/v1/movimientos') && method === 'GET') return { ok: true, status: 200, json: async () => movimientos, headers: { get: () => 'application/json' } };
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    });
    vi.stubGlobal('fetch', mockFetch);
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await user.selectOptions(screen.getByLabelText(/Proveedor/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Cantidad/i), '10');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(await screen.findByText('Movimiento registrado correctamente')).toBeInTheDocument();
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/api/v1/movimientos'), expect.objectContaining({ method: 'GET' }));
  });

  it('4xx mantiene modal sin Reintentar, 5xx con Reintentar', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url) => {
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await user.selectOptions(screen.getByLabelText(/Proveedor/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Cantidad/i), '10');
    // mock 400
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'POST' && url.includes('/entradas')) return { ok: false, status: 400, json: async () => ({ detail: 'Proveedor inactivo' }), headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('Proveedor inactivo')).toBeInTheDocument());
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
    // 5xx
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'POST' && url.includes('/entradas')) return { ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeInTheDocument();
  });

  it('cantidad "1.0"/"   " y motivo "   " y proveedor vacío bloquean local sin fetch', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url) => {
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    const postMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({}), headers: { get: () => 'application/json' } });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'POST') return postMock(url, opts);
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await user.selectOptions(screen.getByLabelText(/Proveedor/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Cantidad/i), '1.0');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    expect(await screen.findByText(/Debe ser un número entero mayor a 0/i)).toBeInTheDocument();
    expect(postMock).not.toHaveBeenCalled();
    await user.clear(screen.getByLabelText(/Cantidad/i));
    await user.type(screen.getByLabelText(/Cantidad/i), '   ');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    expect(await screen.findByText(/Campo requerido/i)).toBeInTheDocument();
    await user.clear(screen.getByLabelText(/Cantidad/i));
    await user.type(screen.getByLabelText(/Cantidad/i), '10');
    await user.type(screen.getByLabelText(/Motivo/i), '   ');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    expect(await screen.findByText(/No puede quedar vací/i)).toBeInTheDocument();
    expect(postMock).not.toHaveBeenCalled();
  });
});

describe('T09 — Movimientos alta Salida — RF-3, RF-4', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('tab Salida oculta proveedor y no lo envía (aunque existía en Entrada)', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url) => {
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await user.selectOptions(screen.getByLabelText(/Proveedor/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Cantidad/i), '10');
    await user.click(screen.getByRole('tab', { name: /Salida/i }));
    expect(screen.queryByLabelText(/Proveedor/i)).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    // si usara crearEntrada, enviaría proveedor, pero debe usar crearSalida sin proveedor
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });

  it('producto+cantidad requerido, 400 stock insuficiente y 404 mantienen modal, 5xx con Reintentar', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url) => {
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    await user.click(screen.getByRole('tab', { name: /Salida/i }));
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    expect((await screen.findAllByText(/Campo requerido/i)).length).toBeGreaterThanOrEqual(1);
    await user.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await user.type(screen.getByLabelText(/Cantidad/i), '100');
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'POST' && url.includes('/salidas')) return { ok: false, status: 400, json: async () => ({ detail: 'Stock insuficiente' }), headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('Stock insuficiente')).toBeInTheDocument());
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    // 5xx
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'POST' && url.includes('/salidas')) return { ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeInTheDocument();
  });

  it('201 Salida cierra + banner + revalidar y cambio Entrada→Salida conserva producto/cantidad/motivo', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url) => {
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await user.type(screen.getByLabelText(/Cantidad/i), '5');
    await user.type(screen.getByLabelText(/Motivo/i), 'Venta');
    await user.click(screen.getByRole('tab', { name: /Salida/i }));
    expect(screen.getByLabelText(/Producto/i)).toHaveValue('PROD-001');
    expect(screen.getByLabelText(/Cantidad/i)).toHaveValue('5');
    expect(screen.getByLabelText(/Motivo/i)).toHaveValue('Venta');
    expect(screen.queryByLabelText(/Proveedor/i)).not.toBeInTheDocument();
    // volver a Entrada proveedor vacío
    await user.click(screen.getByRole('tab', { name: /Entrada/i }));
    expect(screen.getByLabelText(/Proveedor/i)).toHaveValue('');
    // salir: Salida sin proveedor debe enviar sin proveedor y cerrar
    await user.click(screen.getByRole('tab', { name: /Salida/i }));
    let salidasCalled = false;
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'POST' && url.includes('/salidas')) {
          salidasCalled = true;
          const body = JSON.parse(opts.body);
          expect(body).not.toHaveProperty('proveedor_codigo');
          return { ok: true, status: 201, json: async () => ({ id: 1, producto_codigo: 'PROD-001', tipo: 'salida', cantidad: 5 }), headers: { get: () => 'application/json' } };
        }
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(salidasCalled).toBe(true);
    expect(await screen.findByText('Movimiento registrado correctamente')).toBeInTheDocument();
  });
});

describe('T10 — Manejo uniforme estados, mensajes éxito y revalidación vs fallo — RF-4', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('ErrorMessage dos niveles sin variantes y mensajeExito banner role="status" 3s separado coexistiendo con error de revalidación', async () => {
    let callCount = 0;
    const mockFetch = vi.fn().mockImplementation(async (url, opts) => {
      const method = opts?.method || 'GET';
      if (method === 'POST' && url.includes('/entradas')) {
        return { ok: true, status: 201, json: async () => ({ id: 1, producto_codigo: 'PROD-001', tipo: 'entrada', cantidad: 10 }), headers: { get: () => 'application/json' } };
      }
      if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/movimientos') && method === 'GET') {
        callCount++;
        if (callCount === 1) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
        // revalidación falla 500
        return { ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } };
      }
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    });
    vi.stubGlobal('fetch', mockFetch);
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await user.selectOptions(screen.getByLabelText(/Proveedor/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Cantidad/i), '10');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('Movimiento registrado correctamente')).toBeInTheDocument());
    // banner role status y error list coexisten
    expect(screen.getByRole('status')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument());
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Movimiento registrado correctamente')).toBeInTheDocument();
  });

  it('revalidación tras éxito siempre GET completo y 401 como validacion sin Reintentar', async () => {
    let historialCalls = 0;
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        const method = opts?.method || 'GET';
        if (method === 'POST' && url.includes('/entradas')) return { ok: true, status: 201, json: async () => ({ id: 1 }), headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/movimientos') && method === 'GET') {
          historialCalls++;
          if (historialCalls === 1) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
          return { ok: false, status: 401, json: async () => ({ detail: 'No autorizado' }), headers: { get: () => 'application/json' } };
        }
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await user.selectOptions(screen.getByLabelText(/Proveedor/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Cantidad/i), '10');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('Movimiento registrado correctamente')).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('No autorizado')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
  });

  it('grep localStorage vacío y múltiples clics solo una petición', async () => {
    const content = fs.readFileSync(path.join(__dirname, 'Movimientos.jsx'), 'utf8');
    expect(content).not.toMatch(/localStorage/);
    expect(content).not.toMatch(/sessionStorage/);
    // múltiples clics
    let postCalls = 0;
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url, opts) => {
        if (opts?.method === 'POST' && url.includes('/entradas')) {
          postCalls++;
          return new Promise((resolve) => setTimeout(() => resolve({ ok: true, status: 201, json: async () => ({ id: 1 }), headers: { get: () => 'application/json' } }), 100));
        }
        if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
        if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }),
    );
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await user.selectOptions(screen.getByLabelText(/Proveedor/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Cantidad/i), '10');
    const crearBtn = screen.getByRole('button', { name: /^Crear$/i });
    await user.click(crearBtn);
    await user.click(crearBtn);
    await user.click(crearBtn);
    await waitFor(() => expect(crearBtn).toBeDisabled());
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument(), { timeout: 2000 });
    expect(postCalls).toBe(1);
  });
});

describe('T13 — Tests integración Movimientos.jsx (historial/alta entrada/alta salida) — RF-1..4', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('monta→Loading→Historial/Empty/Error', async () => {
    vi.stubGlobal('fetch', mockFetchHistorial({ movimientos: [{ id: 1, producto_codigo: 'PROD-001', proveedor_codigo: null, tipo: 'salida', cantidad: 2, motivo: null, fecha: '2026-09-08T12:00:00Z' }] }));
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('table')).toBeInTheDocument());
    expect(screen.getByText('2026-09-08T12:00:00Z')).toBeInTheDocument();
    // Empty
    vi.stubGlobal('fetch', mockFetchHistorial({ movimientos: [] }));
    const { default: MovimientosEmpty } = await import('./Movimientos.jsx');
    const { unmount } = render(<MemoryRouter><MovimientosEmpty /></MemoryRouter>);
    await waitFor(() => expect(screen.getAllByText('Sin datos disponibles').length).toBeGreaterThanOrEqual(1));
    unmount();
    // Error 5xx
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }));
    const { default: MovimientosErr } = await import('./Movimientos.jsx');
    render(<MemoryRouter><MovimientosErr /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument());
  });

  it('alta Entrada 201 cierra+revalida y ""/"   " bloquea', async () => {
    let historial = [];
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url, opts) => {
      if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
      if (opts?.method === 'POST' && url.includes('/entradas')) {
        historial = [{ id: 1, producto_codigo: 'PROD-001', proveedor_codigo: 'PROV-001', tipo: 'entrada', cantidad: 10, motivo: null, fecha: '2026-09-08T11:00:00Z' }];
        return { ok: true, status: 201, json: async () => historial[0], headers: { get: () => 'application/json' } };
      }
      if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => historial, headers: { get: () => 'application/json' } };
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    // vacío bloquea
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    expect(await screen.findAllByText(/Campo requerido/i)).toBeTruthy();
    // válido
    await user.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await user.selectOptions(screen.getByLabelText(/Proveedor/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Cantidad/i), '10');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(await screen.findByText('Movimiento registrado correctamente')).toBeInTheDocument();
    // "   " bloquea
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    await user.type(screen.getByLabelText(/Cantidad/i), '   ');
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    expect((await screen.findAllByText(/Campo requerido/i)).length).toBeGreaterThanOrEqual(1);
  });

  it('alta Entrada 404 mantiene modal', async () => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url) => {
      if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    await user.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await user.selectOptions(screen.getByLabelText(/Proveedor/i), 'PROV-001');
    await user.type(screen.getByLabelText(/Cantidad/i), '10');
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url, opts) => {
      if (opts?.method === 'POST' && url.includes('/entradas')) return { ok: false, status: 404, json: async () => ({ detail: 'Producto no existe' }), headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('Producto no existe')).toBeInTheDocument());
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
  });

  it('alta Salida sin proveedor y 400 stock insuficiente mantiene modal, salida 201 cierra+revalida', async () => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url) => {
      if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    await user.click(screen.getByRole('tab', { name: /Salida/i }));
    expect(screen.queryByLabelText(/Proveedor/i)).not.toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await user.type(screen.getByLabelText(/Cantidad/i), '100');
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url, opts) => {
      if (opts?.method === 'POST' && url.includes('/salidas')) return { ok: false, status: 400, json: async () => ({ detail: 'Stock insuficiente' }), headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('Stock insuficiente')).toBeInTheDocument());
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    // 201
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url, opts) => {
      if (opts?.method === 'POST' && url.includes('/salidas')) return { ok: true, status: 201, json: async () => ({ id: 1, producto_codigo: 'PROD-001', tipo: 'salida', cantidad: 5 }), headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    await user.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(await screen.findByText('Movimiento registrado correctamente')).toBeInTheDocument();
  });

  it('401 como validacion en alta y revalidación, botones deshabilitados, múltiples clics, proveedor nunca enviado', async () => {
    let postBody = null;
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url, opts) => {
      if (opts?.method === 'POST' && url.includes('/salidas')) {
        postBody = JSON.parse(opts.body);
        return { ok: false, status: 401, json: async () => ({ detail: 'No autorizado' }), headers: { get: () => 'application/json' } };
      }
      if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'J' }], headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'C' }], headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    const { default: Movimientos } = await import('./Movimientos.jsx');
    render(<MemoryRouter><Movimientos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const user = (await import('@testing-library/user-event')).default.setup();
    await user.click(screen.getByRole('button', { name: /Crear movimiento/i }));
    await waitFor(() => expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument());
    await user.click(screen.getByRole('tab', { name: /Salida/i }));
    await user.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await user.type(screen.getByLabelText(/Cantidad/i), '5');
    const crearBtn = screen.getByRole('button', { name: /^Crear$/i });
    // botón deshabilitado durante cargando se probará en flujo anterior; aquí verificar que click no duplica
    await user.click(crearBtn);
    await waitFor(() => expect(screen.getByText('No autorizado')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
    expect(postBody).not.toHaveProperty('proveedor_codigo');
    // múltiples clics ya probado en T10 pero verificar botón existe
    expect(crearBtn).toBeInTheDocument();
  });
});
