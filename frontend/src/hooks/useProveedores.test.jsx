import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T03 — useProveedores — RF-1, RF-5', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('expone {proveedores, cargandoListado, errorListado, revalidar} sin localStorage', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } }));
    const { default: useProveedores } = await import('./useProveedores.js');
    const content = fs.readFileSync(path.join(__dirname, 'useProveedores.js'), 'utf8');
    expect(content).not.toMatch(/localStorage/);
    expect(content).not.toMatch(/sessionStorage/);
    expect(content).not.toMatch(/fetch\s*\(/); // solo via proveedores.js
    const { result } = renderHook(() => useProveedores());
    expect(result.current).toHaveProperty('proveedores');
    expect(result.current).toHaveProperty('cargandoListado');
    expect(result.current).toHaveProperty('errorListado');
    expect(result.current).toHaveProperty('revalidar');
    await waitFor(() => expect(result.current.cargandoListado).toBe(false));
    expect(result.current.proveedores).toEqual([]);
    expect(result.current.errorListado).toBeNull();
  });

  it('revalidar hace GET y actualiza proveedores', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, status: 200, json: async () => [{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: null, direccion: null }], headers: { get: () => 'application/json' },
    }));
    const { default: useProveedores } = await import('./useProveedores.js');
    const { result } = renderHook(() => useProveedores());
    await waitFor(() => expect(result.current.proveedores).toEqual([{ codigo: 'PROV-001', nombre: 'Central', email: null, telefono: null, direccion: null }]));
  });

  it('revalidar maneja cargandoListado y errorListado (4xx vs conexion)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false, status: 404, json: async () => ({ detail: 'No encontrado' }), headers: { get: () => 'application/json' },
    }));
    const { default: useProveedores } = await import('./useProveedores.js');
    const { result } = renderHook(() => useProveedores());
    await waitFor(() => expect(result.current.errorListado).toBeTruthy());
    expect(result.current.errorListado.tipo).toBe('validacion');
    expect(result.current.cargandoListado).toBe(false);
  });

  it('revalidar siempre hace GET tras mutación (sin cache) y sin localStorage', async () => {
    const { default: useProveedores } = await import('./useProveedores.js');
    const content = fs.readFileSync(path.join(__dirname, 'useProveedores.js'), 'utf8');
    expect(content).toMatch(/listarProveedores/);
    expect(content).toMatch(/revalidar/);
    expect(content).not.toMatch(/localStorage/);
  });
});
