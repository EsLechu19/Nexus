import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T02 — useStock — RF-1, RF-2', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it('expone {stock, cargando, error, revalidar} y esFilaStockValida sin localStorage ni fetch directo', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } }));
    const { default: useStock, esFilaStockValida } = await import('./useStock.js');
    const content = fs.readFileSync(path.join(__dirname, 'useStock.js'), 'utf8');
    expect(content).not.toMatch(/localStorage/);
    expect(content).not.toMatch(/sessionStorage/);
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).toMatch(/listarStock/);
    expect(content).toMatch(/esFilaStockValida/);
    expect(typeof esFilaStockValida).toBe('function');
    const { result } = renderHook(() => useStock());
    expect(result.current).toHaveProperty('stock');
    expect(result.current).toHaveProperty('cargando');
    expect(result.current).toHaveProperty('error');
    expect(result.current).toHaveProperty('revalidar');
    await waitFor(() => expect(result.current.cargando).toBe(false));
    expect(result.current.stock).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('esFilaStockValida verifica tipos/presencia de codigo,nombre,stock_actual,stock_minimo,alerta', async () => {
    const { esFilaStockValida } = await import('./useStock.js');
    expect(esFilaStockValida({ codigo: 'PROD-001', nombre: 'Juego', stock_actual: 5, stock_minimo: 10, alerta: true })).toBe(true);
    expect(esFilaStockValida({ codigo: 'PROD-001', nombre: 'Juego', stock_actual: 0, stock_minimo: 0, alerta: false })).toBe(true);
    expect(esFilaStockValida({ codigo: '', nombre: 'Juego', stock_actual: 5, stock_minimo: 10, alerta: true })).toBe(false);
    expect(esFilaStockValida({ codigo: 'PROD-001', nombre: '', stock_actual: 5, stock_minimo: 10, alerta: true })).toBe(false);
    expect(esFilaStockValida({ codigo: 'PROD-001', nombre: 'Juego', stock_actual: '5', stock_minimo: 10, alerta: true })).toBe(false);
    expect(esFilaStockValida({ codigo: 'PROD-001', nombre: 'Juego', stock_actual: 5.5, stock_minimo: 10, alerta: true })).toBe(false);
    expect(esFilaStockValida({ codigo: 'PROD-001', nombre: 'Juego', stock_actual: 5, stock_minimo: 10, alerta: 'true' })).toBe(false);
    expect(esFilaStockValida({ codigo: 'PROD-001', nombre: 'Juego', stock_actual: 5, stock_minimo: 10 })).toBe(false);
    expect(esFilaStockValida({ codigo: 123, nombre: 'Juego', stock_actual: 5, stock_minimo: 10, alerta: true })).toBe(false);
    expect(esFilaStockValida(null)).toBe(false);
    expect(esFilaStockValida(undefined)).toBe(false);
  });

  it('revalidar filtra filas corruptas sin romper resto y todas corruptas → []', async () => {
    const data = [
      { codigo: 'PROD-001', nombre: 'A', stock_actual: 5, stock_minimo: 10, alerta: true },
      { codigo: 'PROD-002', nombre: 'B', stock_actual: '5', stock_minimo: 10, alerta: true },
      { codigo: '', nombre: 'C', stock_actual: 5, stock_minimo: 10, alerta: false },
      { codigo: 'PROD-003', nombre: 'C', stock_actual: 5, stock_minimo: 10, alerta: false },
      { codigo: 'PROD-004', nombre: 'D', stock_actual: 5, stock_minimo: 10, alerta: 'true' },
    ];
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => data, headers: { get: () => 'application/json' } }));
    const { default: useStock } = await import('./useStock.js');
    const { result } = renderHook(() => useStock());
    await waitFor(() => expect(result.current.stock.length).toBe(2));
    expect(result.current.stock.map((s) => s.codigo)).toEqual(['PROD-001', 'PROD-003']);
    // todas corruptas
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [{ codigo: 123, nombre: 'X', stock_actual: 'a', stock_minimo: 0, alerta: 'si' }], headers: { get: () => 'application/json' } }));
    await result.current.revalidar();
    await waitFor(() => expect(result.current.stock).toEqual([]));
  });

  it('revalidar maneja null/204 → [] (EmptyState) y no inventa valores', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => null, headers: { get: () => 'application/json' } }));
    const { default: useStock } = await import('./useStock.js');
    const { result } = renderHook(() => useStock());
    await waitFor(() => expect(result.current.stock).toEqual([]));
    expect(result.current.error).toBeNull();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 204, json: async () => null, headers: { get: () => 'application/json' } }));
    await result.current.revalidar();
    await waitFor(() => expect(result.current.stock).toEqual([]));
  });

  it('revalidar maneja error 401 validacion sin Reintentar y 5xx conexion', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401, json: async () => ({ detail: 'No autorizado' }), headers: { get: () => 'application/json' } }));
    const { default: useStock } = await import('./useStock.js');
    const { result } = renderHook(() => useStock());
    await waitFor(() => expect(result.current.error).toBeTruthy());
    expect(result.current.error.tipo).toBe('validacion');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } }));
    await result.current.revalidar();
    await waitFor(() => expect(result.current.error.tipo).toBe('conexion'));
  });

  it('revalidar siempre hace GET completo y sin localStorage', async () => {
    const content = fs.readFileSync(path.join(__dirname, 'useStock.js'), 'utf8');
    expect(content).toMatch(/listarStock/);
    expect(content).toMatch(/revalidar/);
    expect(content).not.toMatch(/localStorage/);
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } }));
    const { default: useStock } = await import('./useStock.js');
    const { result } = renderHook(() => useStock());
    const first = result.current.revalidar;
    await waitFor(() => expect(result.current.cargando).toBe(false));
    expect(result.current.revalidar).toBe(first);
  });
});
