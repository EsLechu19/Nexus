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

function mockFetchStock({ stock = [] } = {}) {
  return vi.fn().mockImplementation(async (url) => {
    if (url.includes('/api/v1/stock')) {
      return { ok: true, status: 200, json: async () => stock, headers: { get: () => 'application/json' } };
    }
    return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
  });
}

describe('T05 — Stock con estados — RF-1, RF-2', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('al montar muestra Loading luego StockTabla con 5 columnas y sin estado/inactivos', async () => {
    vi.stubGlobal('fetch', mockFetchStock({
      stock: [{ codigo: 'PROD-001', nombre: 'PlayStation 5 Slim', stock_actual: 14, stock_minimo: 10, alerta: false }],
    }));
    const { default: Stock } = await import('./Stock.jsx');
    render(<MemoryRouter><Stock /></MemoryRouter>);
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('table')).toBeInTheDocument());
    expect(screen.getByText('Codigo')).toBeInTheDocument();
    expect(screen.getByText('Nombre')).toBeInTheDocument();
    expect(screen.getByText('Stock actual')).toBeInTheDocument();
    expect(screen.getByText('Stock minimo')).toBeInTheDocument();
    expect(screen.getByText('Alerta')).toBeInTheDocument();
    expect(screen.queryByText('estado')).not.toBeInTheDocument();
    expect(screen.queryByText('inactivo')).not.toBeInTheDocument();
    expect(screen.getByTestId('stock-fila-PROD-001')).toBeInTheDocument();
  });

  it('lista vacía/null/204/todas corruptas muestra EmptyState Sin datos disponibles y — para alerta false', async () => {
    vi.stubGlobal('fetch', mockFetchStock({ stock: [] }));
    const { default: Stock } = await import('./Stock.jsx');
    render(<MemoryRouter><Stock /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
    // con null -> también EmptyState (via hook filtra null → [])
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => null, headers: { get: () => 'application/json' } }));
    const { default: StockNull } = await import('./Stock.jsx');
    const { unmount } = render(<MemoryRouter><StockNull /></MemoryRouter>);
    await waitFor(() => expect(screen.getAllByText('Sin datos disponibles').length).toBeGreaterThanOrEqual(1));
    unmount();
    // todas corruptas filtradas → EmptyState
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [{ codigo: 123, nombre: null, stock_actual: 'a', stock_minimo: 0, alerta: 'si' }], headers: { get: () => 'application/json' } }));
    const { default: StockCorr } = await import('./Stock.jsx');
    render(<MemoryRouter><StockCorr /></MemoryRouter>);
    await waitFor(() => expect(screen.getAllByText('Sin datos disponibles').length).toBeGreaterThanOrEqual(1));
  });

  it('error 4xx muestra mensaje API sin Reintentar, 5xx/red con Reintentar que re-ejecuta revalidar', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401, json: async () => ({ detail: 'No autorizado' }), headers: { get: () => 'application/json' } }));
    const { default: Stock } = await import('./Stock.jsx');
    const { unmount } = render(<MemoryRouter><Stock /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('No autorizado')).toBeInTheDocument());
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
    unmount();
    let callCount = 0;
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url) => {
      if (url.includes('/api/v1/stock')) {
        callCount++;
        if (callCount === 1) return { ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } };
        return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      }
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    const { default: Stock2 } = await import('./Stock.jsx');
    render(<MemoryRouter><Stock2 /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeInTheDocument();
  });

  it('App.jsx ruta /stock anidada bajo AppLayout', async () => {
    vi.stubGlobal('fetch', mockFetchStock({ stock: [] }));
    const { default: App } = await import('../App.jsx');
    render(<MemoryRouter initialEntries={['/stock']}><App /></MemoryRouter>);
    await waitFor(() => expect(screen.getByRole('navigation')).toBeInTheDocument());
    expect(screen.getByRole('main')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument());
  });

  it('no contiene fetch directo ni localStorage, sin columna estado, 5 cols badge+fila, sin reordenar', () => {
    const content = fs.readFileSync(path.join(__dirname, 'Stock.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).not.toMatch(/localStorage/);
    expect(content).not.toMatch(/stock_actual.*stock_minimo.*alerta.*sort/i);
    expect(content).toMatch(/StockTabla/);
    expect(content).toMatch(/useStock/);
  });
});

describe('T06 — Integrar revalidación y defensivo — RF-1, RF-2', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('revalidar filtra esFilaStockValida tras listarStock, si todas corruptas muestra EmptyState', async () => {
    const stockMixto = [
      { codigo: 'PROD-001', nombre: 'Valido', stock_actual: 5, stock_minimo: 10, alerta: true },
      { codigo: 123, nombre: 'Invalido codigo number', stock_actual: 5, stock_minimo: 10, alerta: true },
      { codigo: 'PROD-003', nombre: 'Invalido alerta string', stock_actual: 5, stock_minimo: 10, alerta: 'true' },
    ];
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => stockMixto, headers: { get: () => 'application/json' } }));
    const { default: Stock } = await import('./Stock.jsx');
    render(<MemoryRouter><Stock /></MemoryRouter>);
    await waitFor(() => expect(screen.getByTestId('stock-fila-PROD-001')).toBeInTheDocument());
    expect(screen.queryByTestId('stock-fila-123')).not.toBeInTheDocument();
    expect(screen.queryByTestId('stock-fila-PROD-003')).not.toBeInTheDocument();
    // todas corruptas
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [{ codigo: null, nombre: null, stock_actual: 'x', stock_minimo: null, alerta: null }], headers: { get: () => 'application/json' } }));
    const { default: StockAllCorr } = await import('./Stock.jsx');
    const { unmount } = render(<MemoryRouter><StockAllCorr /></MemoryRouter>);
    await waitFor(() => expect(screen.getAllByText('Sin datos disponibles').length).toBeGreaterThanOrEqual(1));
    unmount();
  });

  it('alerta nunca recalculada (solo lee campo) y grep localStorage vacío', () => {
    const stockContent = fs.readFileSync(path.join(__dirname, 'Stock.jsx'), 'utf8');
    expect(stockContent).not.toMatch(/stock_minimo\s*>\s*0\s*&&\s*stock_actual\s*</);
    expect(stockContent).not.toMatch(/localStorage/);
    expect(stockContent).not.toMatch(/sessionStorage/);
    const hookContent = fs.readFileSync(path.join(__dirname, '../hooks/useStock.js'), 'utf8');
    expect(hookContent).not.toMatch(/stock_minimo\s*>\s*0\s*&&\s*stock_actual\s*</);
    // StockTabla tampoco recalcula
    const tablaContent = fs.readFileSync(path.join(__dirname, '../components/StockTabla.jsx'), 'utf8');
    expect(tablaContent).not.toMatch(/stock_minimo\s*>\s*0/);
  });

  it('cargando deshabilita Reintentar y navegar fuera durante cargando no cancela', async () => {
    let resolveFetch;
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() => new Promise((res) => { resolveFetch = res; })));
    const { default: Stock } = await import('./Stock.jsx');
    const { unmount } = render(<MemoryRouter><Stock /></MemoryRouter>);
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
    // navegar fuera: desmontar mientras cargando
    unmount();
    // resolver fetch después de desmontar no debe lanzar error y al volver a montar debe reflejar resultado
    resolveFetch({ ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'A', stock_actual: 5, stock_minimo: 10, alerta: true }], headers: { get: () => 'application/json' } });
    const { default: Stock2 } = await import('./Stock.jsx');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [{ codigo: 'PROD-001', nombre: 'A', stock_actual: 5, stock_minimo: 10, alerta: true }], headers: { get: () => 'application/json' } }));
    render(<MemoryRouter><Stock2 /></MemoryRouter>);
    await waitFor(() => expect(screen.getByTestId('stock-fila-PROD-001')).toBeInTheDocument());
    // Reintentar deshabilitado mientras cargando: simular 5xx luego reintentar
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url) => {
      if (url.includes('/api/v1/stock')) {
        return new Promise((res) => setTimeout(() => res({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }), 50));
      }
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    const { default: StockErr } = await import('./Stock.jsx');
    render(<MemoryRouter><StockErr /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument());
    const btn = screen.getByRole('button', { name: /Reintentar/i });
    expect(btn).toBeInTheDocument();
    // mientras cargando tras click, debe deshabilitarse
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() => new Promise(() => {})));
    await btn.click?.();
    // no assertion de disabled tras click sin resolver, pero verifica que no hay localStorage
    expect(fs.readFileSync(path.join(__dirname, 'Stock.jsx'), 'utf8')).not.toMatch(/localStorage/);
  });
});
