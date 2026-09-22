import { request } from './client.js';

/**
 * API de stock — RF-1, RF-2
 * Usa cliente centralizado de 005 (request tipado).
 * No hace fetch directo (constitución §3).
 * Lee campo alerta boolean ya calculado por backend, nunca recalcula.
 */

export function listarStock() {
  return request('/api/v1/stock', { method: 'GET' });
}
