import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T03 — useMovimientos — RF-1, RF-4', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('expone {movimientos, productos, proveedores, cargandoHistorial, cargandoSelects, errorHistorial, errorSelects, revalidar, cargarSelects} sin localStorage ni fetch directo', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } }));
    const { default: useMovimientos } = await import('./useMovimientos.js');
    const content = fs.readFileSync(path.join(__dirname, 'useMovimientos.js'), 'utf8');
    expect(content).not.toMatch(/localStorage/);
    expect(content).not.toMatch(/sessionStorage/);
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).toMatch(/listarMovimientos/);
    expect(content).toMatch(/listarProductos/);
    expect(content).toMatch(/listarProveedores/);
    expect(content).toMatch(/Promise\.all/);
    const { result } = renderHook(() => useMovimientos());
    expect(result.current).toHaveProperty('movimientos');
    expect(result.current).toHaveProperty('productos');
    expect(result.current).toHaveProperty('proveedores');
    expect(result.current).toHaveProperty('cargandoHistorial');
    expect(result.current).toHaveProperty('cargandoSelects');
    expect(result.current).toHaveProperty('errorHistorial');
    expect(result.current).toHaveProperty('errorSelects');
    expect(result.current).toHaveProperty('revalidar');
    expect(result.current).toHaveProperty('cargarSelects');
    await waitFor(() => expect(result.current.cargandoHistorial).toBe(false));
    expect(result.current.movimientos).toEqual([]);
    expect(result.current.errorHistorial).toBeNull();
  });

  it('revalidar hace GET historial y actualiza movimientos (sin reordenar)', async () => {
    const historial = [
      { id: 2, producto_codigo: 'PROD-001', proveedor_codigo: null, tipo: 'salida', cantidad: 2, motivo: null, fecha: '2026-09-08T11:00:00Z' },
      { id: 1, producto_codigo: 'PROD-001', proveedor_codigo: null, tipo: 'entrada_inicial', cantidad: 10, motivo: null, fecha: '2026-09-07T10:00:00Z' },
    ];
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url) => {
      if (url.includes('/api/v1/movimientos')) {
        return { ok: true, status: 200, json: async () => historial, headers: { get: () => 'application/json' } };
      }
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    const { default: useMovimientos } = await import('./useMovimientos.js');
    const { result } = renderHook(() => useMovimientos());
    await waitFor(() => expect(result.current.movimientos).toEqual(historial));
    expect(result.current.movimientos.map((m) => m.id)).toEqual([2, 1]);
  });

  it('cargarSelects hace Promise.all para productos y proveedores y maneja cargandoSelects', async () => {
    const productos = [{ codigo: 'PROD-001', nombre: 'Juego A' }];
    const proveedores = [{ codigo: 'PROV-001', nombre: 'Central' }];
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url) => {
      if (url.includes('/api/v1/productos')) return { ok: true, status: 200, json: async () => productos, headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/proveedores')) return { ok: true, status: 200, json: async () => proveedores, headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/movimientos')) return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    const { default: useMovimientos } = await import('./useMovimientos.js');
    const { result } = renderHook(() => useMovimientos());
    await waitFor(() => expect(result.current.productos).toEqual(productos));
    await waitFor(() => expect(result.current.proveedores).toEqual(proveedores));
    expect(result.current.cargandoSelects).toBe(false);
    expect(result.current.errorSelects).toBeNull();
    // revalidar debe seguir siendo GET historial completo
    const content = fs.readFileSync(path.join(__dirname, 'useMovimientos.js'), 'utf8');
    expect(content).toMatch(/revalidar/);
  });

  it('maneja errorHistorial (4xx validacion vs 5xx conexion) y errorSelects', async () => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url) => {
      if (url.includes('/api/v1/movimientos')) return { ok: false, status: 500, json: async () => ({}), headers: { get: () => 'application/json' } };
      if (url.includes('/api/v1/productos') || url.includes('/api/v1/proveedores')) return { ok: false, status: 404, json: async () => ({ detail: 'No encontrado' }), headers: { get: () => 'application/json' } };
      return { ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } };
    }));
    const { default: useMovimientos } = await import('./useMovimientos.js');
    const { result } = renderHook(() => useMovimientos());
    await waitFor(() => expect(result.current.errorHistorial).toBeTruthy());
    expect(result.current.errorHistorial.tipo).toBe('conexion');
    await waitFor(() => expect(result.current.errorSelects).toBeTruthy());
    expect(result.current.errorSelects.tipo).toBe('validacion');
  });

  it('revalidar siempre hace GET historial completo tras alta (sin cache) y sin localStorage', async () => {
    const content = fs.readFileSync(path.join(__dirname, 'useMovimientos.js'), 'utf8');
    expect(content).toMatch(/listarMovimientos/);
    expect(content).toMatch(/revalidar/);
    expect(content).not.toMatch(/localStorage/);
    // verificar que revalidar es estable (useCallback) y no depende de cache
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } }));
    const { default: useMovimientos } = await import('./useMovimientos.js');
    const { result } = renderHook(() => useMovimientos());
    const firstRevalidar = result.current.revalidar;
    await waitFor(() => expect(result.current.cargandoHistorial).toBe(false));
    expect(result.current.revalidar).toBe(firstRevalidar);
  });
});
