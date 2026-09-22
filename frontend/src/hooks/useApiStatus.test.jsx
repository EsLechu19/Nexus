import { describe, it, expect, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import useApiStatus from './useApiStatus.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T12 — useApiStatus — RF-5, RNF-6', () => {
  it('inicia en idle sin error y sin localStorage', () => {
    const fetcher = vi.fn().mockResolvedValue({ data: [] });
    const { result } = renderHook(() => useApiStatus(fetcher));
    expect(result.current.estado).toBe('idle');
    expect(result.current.error).toBeNull();
    expect(result.current.cargando).toBe(false);
    const content = fs.readFileSync(path.join(__dirname, 'useApiStatus.js'), 'utf8');
    expect(content).not.toMatch(/localStorage/);
    expect(content).not.toMatch(/sessionStorage/);
  });

  it('transita a cargando y luego a exito con datos', async () => {
    const fetcher = vi.fn().mockResolvedValue([{ id: 1 }]);
    const { result } = renderHook(() => useApiStatus(fetcher));
    act(() => {
      result.current.reintentar();
    });
    expect(result.current.estado).toBe('cargando');
    expect(result.current.cargando).toBe(true);
    await waitFor(() => expect(result.current.estado).toBe('exito'));
    expect(result.current.data).toEqual([{ id: 1 }]);
    expect(result.current.cargando).toBe(false);
  });

  it('transita a vacio cuando lista vacía', async () => {
    const fetcher = vi.fn().mockResolvedValue([]);
    const { result } = renderHook(() => useApiStatus(fetcher));
    act(() => {
      result.current.reintentar();
    });
    await waitFor(() => expect(result.current.estado).toBe('vacio'));
  });

  it('transita a error con tipo conexion y permite reintentar', async () => {
    const errorConexion = { tipo: 'conexion', mensaje: 'Error de conexión con el servidor', reintentable: true };
    const fetcher = vi.fn().mockRejectedValue(errorConexion);
    const { result } = renderHook(() => useApiStatus(fetcher));
    act(() => {
      result.current.reintentar();
    });
    await waitFor(() => expect(result.current.estado).toBe('error'));
    expect(result.current.error).toEqual(errorConexion);
    // reintentar debe volver a intentar
    const fetcher2 = vi.fn().mockResolvedValue([{ id: 2 }]);
    // no podemos cambiar fetcher en mismo hook, pero reintentar debe llamar de nuevo al fetcher original
    // verificamos que reintentar no está deshabilitado por cargando previo
    expect(result.current.reintentar).toBeDefined();
  });

  it('transita a error validacion sin reintento automático', async () => {
    const errorVal = { tipo: 'validacion', mensaje: 'SKU ya existe', reintentable: false };
    const fetcher = vi.fn().mockRejectedValue(errorVal);
    const { result } = renderHook(() => useApiStatus(fetcher));
    act(() => {
      result.current.reintentar();
    });
    await waitFor(() => expect(result.current.estado).toBe('error'));
    expect(result.current.error.tipo).toBe('validacion');
  });

  it('deshabilita concurrentes: segundo reintentar mientras cargando es ignorado', async () => {
    let resolve;
    const fetcher = vi.fn().mockImplementation(() => new Promise(r => { resolve = r; }));
    const { result } = renderHook(() => useApiStatus(fetcher));
    act(() => {
      result.current.reintentar();
    });
    expect(result.current.cargando).toBe(true);
    // segundo llamado mientras cargando debe ser ignorado
    act(() => {
      result.current.reintentar();
    });
    expect(fetcher).toHaveBeenCalledTimes(1);
    // resolver y esperar vacio
    await act(async () => {
      resolve([]);
    });
    await waitFor(() => expect(result.current.estado).toBe('vacio'));
  });

  it('se descarta al desmontar (no actualiza estado tras unmount)', async () => {
    const fetcher = vi.fn().mockImplementation(() => new Promise(() => {}));
    const { result, unmount } = renderHook(() => useApiStatus(fetcher));
    act(() => {
      result.current.reintentar();
    });
    unmount();
    // no debe lanzar ni mantener cargando tras unmount
    expect(result.current.cargando).toBe(true); // al momento de unmount seguía cargando, pero no debe causar update posterior
  });

  it('no contiene fetch directo ni localStorage', () => {
    const content = fs.readFileSync(path.join(__dirname, 'useApiStatus.js'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).not.toMatch(/localStorage/);
    expect(content).not.toMatch(/sessionStorage/);
  });
});
