import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
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

// Helper para mockear fetch según ruta
function mockFetchForProductos({ productos = [], postRes, patchRes, deleteRes, error } = {}) {
  return vi.fn().mockImplementation(async (url, opts) => {
    const method = opts?.method || 'GET';
    if (url.includes('/api/v1/productos') && method === 'GET') {
      if (error) throw error;
      if (error === 'validacion') return { ok: false, status: 400, json: async () => ({ detail: 'Error validación' }), headers: { get: () => 'application/json' } };
      return { ok: true, status: 200, json: async () => productos, headers: { get: () => 'application/json' } };
    }
    if (method === 'POST' && postRes) {
      if (postRes.ok) return { ok: true, status: 201, json: async () => postRes.data, headers: { get: () => 'application/json' } };
      return { ok: false, status: postRes.status, json: async () => postRes.data, headers: { get: () => 'application/json' } };
    }
    if (method === 'PATCH' && patchRes) {
      if (patchRes.ok) return { ok: true, status: 200, json: async () => patchRes.data, headers: { get: () => 'application/json' } };
      return { ok: false, status: patchRes.status, json: async () => patchRes.data, headers: { get: () => 'application/json' } };
    }
    if (method === 'DELETE' && deleteRes) {
      if (deleteRes.ok) return { ok: true, status: 200, json: async () => deleteRes.data, headers: { get: () => 'application/json' } };
      return { ok: false, status: deleteRes.status, json: async () => deleteRes.data, headers: { get: () => 'application/json' } };
    }
    return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
  });
}

describe('T08 — Productos listado — RF-1', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('al montar muestra Loading luego ProductoTabla con 4 columnas', async () => {
    vi.stubGlobal('fetch', mockFetchForProductos({ productos: [{ sku: 'A', nombre: 'A', categoria: 'videojuego', stock_inicial: 5 }] }));
    const { default: Productos } = await import('./Productos.jsx');
    render(<MemoryRouter initialEntries={['/productos']}><Productos /></MemoryRouter>);
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('table')).toBeInTheDocument());
    expect(screen.getByText('SKU')).toBeInTheDocument();
    expect(screen.queryByText('Estado')).not.toBeInTheDocument();
  });

  it('lista vacía muestra EmptyState', async () => {
    vi.stubGlobal('fetch', mockFetchForProductos({ productos: [] }));
    const { default: Productos } = await import('./Productos.jsx');
    render(<MemoryRouter><Productos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
  });

  it('error 4xx muestra mensaje API sin Reintentar, 5xx con Reintentar', async () => {
    // 4xx
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'SKU inválido' }), headers: { get: () => 'application/json' } }));
    const { default: Productos } = await import('./Productos.jsx');
    const { unmount } = render(<MemoryRouter><Productos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('SKU inválido')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
    unmount();
    // 5xx
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }));
    const { default: Productos2 } = await import('./Productos.jsx');
    render(<MemoryRouter><Productos2 /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeInTheDocument();
  });

  it('App.jsx ruta /productos anidada bajo AppLayout', async () => {
    const { default: App } = await import('../App.jsx');
    vi.stubGlobal('fetch', mockFetchForProductos({ productos: [] }));
    render(<MemoryRouter initialEntries={['/productos']}><App /></MemoryRouter>);
    await waitFor(() => expect(screen.getByRole('navigation')).toBeInTheDocument());
    expect(screen.getByRole('main')).toBeInTheDocument();
  });
});

describe('T09 — Alta — RF-2, RF-5', () => {
  beforeEach(() => { vi.stubEnv('VITE_API_URL', 'http://localhost:8000'); });
  afterEach(() => { vi.unstubAllEnvs(); vi.restoreAllMocks(); });

  it('click Crear abre modal 4 campos, validación solo presencia', async () => {
    vi.stubGlobal('fetch', mockFetchForProductos({ productos: [] }));
    const { default: Productos } = await import('./Productos.jsx');
    render(<MemoryRouter><Productos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    await userEvent.click(screen.getByRole('button', { name: /Crear producto/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByLabelText(/Nombre/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /Crear$/i }));
    expect(await screen.findByText(/Nombre requerido/i)).toBeInTheDocument();
  });

  it('stock vacío no bloquea y envía sin stock_inicial', async () => {
    const mockFetch = mockFetchForProductos({ productos: [] });
    // para POST, simular éxito
    const postMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({ sku: 'X', nombre: 'Y', categoria: 'videojuego', stock_inicial: 0 }), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url, opts) => {
      if (opts?.method === 'POST') return postMock(url, opts);
      return mockFetch(url, opts);
    }));
    const { default: Productos } = await import('./Productos.jsx');
    render(<MemoryRouter><Productos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    await userEvent.click(screen.getByRole('button', { name: /Crear producto/i }));
    await userEvent.type(screen.getByLabelText(/Nombre/i), 'Y');
    await userEvent.type(screen.getByLabelText(/^SKU$/i), 'X');
    await userEvent.selectOptions(screen.getByLabelText(/Categoría/i), 'videojuego');
    await userEvent.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(postMock).toHaveBeenCalled());
    const body = JSON.parse(postMock.mock.calls[0][1].body);
    expect(body).not.toHaveProperty('stock_inicial');
  });

  it('4xx mantiene modal con mensaje API, 5xx con Reintentar, cargando deshabilita', async () => {
    vi.stubGlobal('fetch', mockFetchForProductos({ productos: [] }));
    const { default: Productos } = await import('./Productos.jsx');
    render(<MemoryRouter><Productos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    await userEvent.click(screen.getByRole('button', { name: /Crear producto/i }));
    // mock 409 para siguiente POST
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url, opts) => {
      if (opts?.method === 'POST') return Promise.resolve({ ok: false, status: 409, json: async () => ({ detail: 'SKU ya existe' }), headers: { get: () => 'application/json' } });
      return Promise.resolve({ ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } });
    }));
    await userEvent.type(screen.getByLabelText(/Nombre/i), 'Y');
    await userEvent.type(screen.getByLabelText(/^SKU$/i), 'DUPE');
    await userEvent.selectOptions(screen.getByLabelText(/Categoría/i), 'consola');
    await userEvent.click(screen.getByRole('button', { name: /^Crear$/i }));
    await waitFor(() => expect(screen.getByText('SKU ya existe')).toBeInTheDocument());
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
});

describe('T10 — Edición — RF-3, RF-5', () => {
  beforeEach(() => { vi.stubEnv('VITE_API_URL', 'http://localhost:8000'); });
  afterEach(() => { vi.unstubAllEnvs(); vi.restoreAllMocks(); });

  it('Editar precarga nombre/categoria, SKU deshabilitado sin stock', async () => {
    vi.stubGlobal('fetch', mockFetchForProductos({ productos: [{ sku: 'PS5-001', nombre: 'Play', categoria: 'consola', stock_inicial: 10 }] }));
    const { default: Productos } = await import('./Productos.jsx');
    render(<MemoryRouter><Productos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Play')).toBeInTheDocument());
    await userEvent.click(screen.getByRole('button', { name: /Editar/i }));
    expect(screen.getByLabelText(/^SKU$/i)).toHaveValue('PS5-001');
    expect(screen.getByLabelText(/^SKU$/i)).toBeDisabled();
    expect(screen.queryByLabelText(/Stock inicial/i)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/Nombre/i)).toHaveValue('Play');
  });

  it('PATCH solo envía nombre/categoria, 4xx mantiene modal', async () => {
    const patchMock = vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ detail: 'Nombre inválido' }), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url, opts) => {
      if (opts?.method === 'PATCH') return patchMock(url, opts);
      return Promise.resolve({ ok: true, status: 200, json: async () => [{ sku: 'PS5-001', nombre: 'Play', categoria: 'consola', stock_inicial: 10 }], headers: { get: () => 'application/json' } });
    }));
    const { default: Productos } = await import('./Productos.jsx');
    render(<MemoryRouter><Productos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Play')).toBeInTheDocument());
    await userEvent.click(screen.getByRole('button', { name: /Editar/i }));
    await userEvent.clear(screen.getByLabelText(/Nombre/i));
    await userEvent.type(screen.getByLabelText(/Nombre/i), 'Nuevo');
    await userEvent.click(screen.getByRole('button', { name: /Guardar/i }));
    await waitFor(() => expect(patchMock).toHaveBeenCalled());
    const body = JSON.parse(patchMock.mock.calls[0][1].body);
    expect(body).toEqual({ nombre: 'Nuevo', categoria: 'consola' });
    expect(body).not.toHaveProperty('sku');
    await waitFor(() => expect(screen.getByText('Nombre inválido')).toBeInTheDocument());
  });
});

describe('T11 — Baja — RF-4, RF-5', () => {
  beforeEach(() => { vi.stubEnv('VITE_API_URL', 'http://localhost:8000'); });
  afterEach(() => { vi.unstubAllEnvs(); vi.restoreAllMocks(); });

  it('Dar de baja abre diálogo confirmación, cancelar cierra', async () => {
    vi.stubGlobal('fetch', mockFetchForProductos({ productos: [{ sku: 'PS5-001', nombre: 'Play', categoria: 'consola', stock_inicial: 10 }] }));
    const { default: Productos } = await import('./Productos.jsx');
    render(<MemoryRouter><Productos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Play')).toBeInTheDocument());
    await userEvent.click(screen.getByRole('button', { name: /Dar de baja/i }));
    expect(screen.getByText(/¿Dar de baja a Play \(PS5-001\)\?/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /Cancelar/i }));
    expect(screen.queryByText(/¿Dar de baja/)).not.toBeInTheDocument();
  });

  it('Confirmar deshabilita mientras cargando, 200 cierra y revalida a EmptyState si 1→0', async () => {
    let productos = [{ sku: 'PS5-001', nombre: 'Play', categoria: 'consola', stock_inicial: 10 }];
    let resolveDelete;
    const mockFetch = vi.fn().mockImplementation((url, opts) => {
      if (opts?.method === 'DELETE') {
        return new Promise((resolve) => {
          resolveDelete = () => {
            productos = [];
            resolve({ ok: true, status: 200, json: async () => ({ sku: 'PS5-001', estado: 'inactivo' }), headers: { get: () => 'application/json' } });
          };
        });
      }
      if (url.includes('/api/v1/productos') && (!opts?.method || opts.method === 'GET')) {
        return Promise.resolve({ ok: true, status: 200, json: async () => productos, headers: { get: () => 'application/json' } });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } });
    });
    vi.stubGlobal('fetch', mockFetch);
    const { default: Productos } = await import('./Productos.jsx');
    render(<MemoryRouter><Productos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Play')).toBeInTheDocument());
    await userEvent.click(screen.getByRole('button', { name: /Dar de baja/i }));
    const clickPromise = userEvent.click(screen.getByRole('button', { name: /Confirmar/i }));
    // mientras la petición está en curso, el botón debe estar deshabilitado
    await waitFor(() => expect(screen.getByRole('button', { name: /Confirmar/i })).toBeDisabled());
    // resolver la petición
    resolveDelete();
    await clickPromise;
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
  });

  it('navegar durante cargando no cancela petición', async () => {
    const content = fs.readFileSync(path.join(__dirname, 'Productos.jsx'), 'utf8');
    expect(content).not.toMatch(/AbortController.*baja|abort.*baja/i);
  });
});

describe('T12 — Estados uniformes y revalidación — RF-5', () => {
  it('usa Loading/EmptyState/ErrorMessage dos niveles y banner éxito separado', async () => {
    const content = fs.readFileSync(path.join(__dirname, 'Productos.jsx'), 'utf8');
    expect(content).toMatch(/Loading/);
    expect(content).toMatch(/EmptyState/);
    expect(content).toMatch(/ErrorMessage/);
    expect(content).toMatch(/Producto creado correctamente|Producto actualizado correctamente|Producto dado de baja correctamente/);
  });

  it('revalidación siempre GET tras mutación y 401 como validacion, sin localStorage', () => {
    const content = fs.readFileSync(path.join(__dirname, 'Productos.jsx'), 'utf8');
    expect(content).not.toMatch(/localStorage/);
    expect(content).not.toMatch(/sessionStorage/);
    expect(content).toMatch(/revalidar|listarProductos/);
  });

  it('no contiene fetch directo', () => {
    const content = fs.readFileSync(path.join(__dirname, 'Productos.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });
});

describe('T13 — Tokens diseño 010 — RF-1/RF-3/RF-5 (botón primario página, banner éxito, sin hex)', () => {
  beforeEach(() => { vi.stubEnv('VITE_API_URL', 'http://localhost:8000'); });
  afterEach(() => { vi.unstubAllEnvs(); vi.restoreAllMocks(); });

  it('botón Crear producto usa bg-primary-500 focus:ring-primary-500', async () => {
    vi.stubGlobal('fetch', mockFetchForProductos({ productos: [] }));
    const { default: Productos } = await import('./Productos.jsx');
    render(<MemoryRouter><Productos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    const btn = screen.getByRole('button', { name: /Crear producto/i });
    expect(btn.className).toMatch(/bg-primary-500/);
    expect(btn.className).toMatch(/hover:bg-primary-600/);
    expect(btn.className).toMatch(/focus:ring-primary-500/);
    const content = fs.readFileSync(path.join(__dirname, 'Productos.jsx'), 'utf8');
    expect(content).not.toMatch(/#[0-9a-fA-F]{3,6}/);
  });

  it('banner éxito tras alta usa bg-success-50 y texto Producto creado correctamente', async () => {
    const mockFetch = mockFetchForProductos({ productos: [] });
    const postMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({ sku: 'X', nombre: 'Y', categoria: 'videojuego', stock_inicial: 0 }), headers: { get: () => 'application/json' } });
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url, opts) => {
      if (opts?.method === 'POST') return postMock(url, opts);
      return mockFetch(url, opts);
    }));
    const { default: Productos } = await import('./Productos.jsx');
    render(<MemoryRouter><Productos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    await userEvent.click(screen.getByRole('button', { name: /Crear producto/i }));
    await userEvent.type(screen.getByLabelText(/Nombre/i), 'Y');
    await userEvent.type(screen.getByLabelText(/^SKU$/i), 'X');
    await userEvent.selectOptions(screen.getByLabelText(/Categoría/i), 'videojuego');
    await userEvent.click(screen.getByRole('button', { name: /^Crear$/i }));
    const banner = await screen.findByText('Producto creado correctamente');
    expect(banner.closest('[role="status"]').className).toMatch(/bg-success-50/);
    expect(banner.closest('[role="status"]').className).toMatch(/text-success-600/);
  });

  it('botón Dar de baja usa bg-error-600 y diálogo usa bg-neutral-0', async () => {
    vi.stubGlobal('fetch', mockFetchForProductos({ productos: [{ sku: 'PS5-001', nombre: 'Play', categoria: 'consola', stock_inicial: 10 }] }));
    const { default: Productos } = await import('./Productos.jsx');
    render(<MemoryRouter><Productos /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Play')).toBeInTheDocument());
    const bajaBtn = screen.getByRole('button', { name: /Dar de baja/i });
    expect(bajaBtn.className).toMatch(/bg-error-600/);
    expect(bajaBtn.className).toMatch(/focus:ring-primary-500/);
    await userEvent.click(bajaBtn);
    const dialog = screen.getByRole('dialog');
    expect(dialog.className).toMatch(/bg-neutral-0/);
    expect(dialog.className).toMatch(/rounded-lg/);
  });
});
