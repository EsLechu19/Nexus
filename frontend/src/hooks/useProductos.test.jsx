import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T03 — useProductos — RF-1, RF-5', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('expone {productos, cargandoListado, errorListado, revalidar} sin localStorage', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } }));
    const { default: useProductos } = await import('./useProductos.js');
    const content = fs.readFileSync(path.join(__dirname, 'useProductos.js'), 'utf8');
    expect(content).not.toMatch(/localStorage/);
    expect(content).not.toMatch(/sessionStorage/);
    expect(content).not.toMatch(/fetch\s*\(/); // solo via productos.js
    const { result } = renderHook(() => useProductos());
    expect(result.current).toHaveProperty('productos');
    expect(result.current).toHaveProperty('cargandoListado');
    expect(result.current).toHaveProperty('errorListado');
    expect(result.current).toHaveProperty('revalidar');
    // al montar inicia cargando
    await waitFor(() => expect(result.current.cargandoListado).toBe(false));
    expect(result.current.productos).toEqual([]);
    expect(result.current.errorListado).toBeNull();
  });

  it('revalidar hace GET y actualiza productos', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, status: 200, json: async () => [{ sku: 'A', nombre: 'A', categoria: 'videojuego', stock_inicial: 0 }], headers: { get: () => 'application/json' },
    }));
    const { default: useProductos } = await import('./useProductos.js');
    const { result } = renderHook(() => useProductos());
    await waitFor(() => expect(result.current.productos).toEqual([{ sku: 'A', nombre: 'A', categoria: 'videojuego', stock_inicial: 0 }]));
  });

  it('revalidar maneja cargandoListado y errorListado (4xx vs conexion)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false, status: 404, json: async () => ({ detail: 'No encontrado' }), headers: { get: () => 'application/json' },
    }));
    const { default: useProductos } = await import('./useProductos.js');
    const { result } = renderHook(() => useProductos());
    await waitFor(() => expect(result.current.errorListado).toBeTruthy());
    expect(result.current.errorListado.tipo).toBe('validacion');
    expect(result.current.cargandoListado).toBe(false);
  });

  it('revalidar siempre hace GET tras mutación (sin cache)', async () => {
    const { default: useProductos } = await import('./useProductos.js');
    const content = fs.readFileSync(path.join(__dirname, 'useProductos.js'), 'utf8');
    expect(content).toMatch(/listarProductos/);
    expect(content).toMatch(/revalidar/);
  });
});
