import { request } from './client.js';

/**
 * API de movimientos — RF-1..4
 * Usa cliente centralizado de 005 (request tipado).
 * No hace fetch directo (constitución §3).
 */

export function listarMovimientos() {
  return request('/api/v1/movimientos', { method: 'GET' });
}

export function crearEntrada({ producto_codigo, proveedor_codigo, cantidad, motivo }) {
  const body = { producto_codigo, proveedor_codigo, cantidad };
  if (motivo !== undefined && motivo !== null && motivo !== '') {
    body.motivo = motivo;
  }
  return request('/api/v1/movimientos/entradas', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function crearSalida({ producto_codigo, cantidad, motivo }) {
  const body = { producto_codigo, cantidad };
  if (motivo !== undefined && motivo !== null && motivo !== '') {
    body.motivo = motivo;
  }
  return request('/api/v1/movimientos/salidas', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}
