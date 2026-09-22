import { request } from './client.js';

/**
 * API de productos — RF-1..4
 * Usa cliente centralizado de 005 (request tipado).
 * No hace fetch directo (constitución §3).
 */

export function listarProductos() {
  return request('/api/v1/productos', { method: 'GET' });
}

export function crearProducto({ nombre, sku, categoria, stock_inicial }) {
  const body = { nombre, sku, categoria };
  // stock_inicial vacío (null/undefined) → ausencia para que backend trate como 0 sin traza
  if (stock_inicial !== undefined && stock_inicial !== null && stock_inicial !== '') {
    body.stock_inicial = stock_inicial;
  }
  return request('/api/v1/productos', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function editarProducto(sku, { nombre, categoria }) {
  const body = {};
  if (nombre !== undefined) body.nombre = nombre;
  if (categoria !== undefined) body.categoria = categoria;
  // nunca enviar sku, stock_inicial ni estado (RF-3)
  return request(`/api/v1/productos/${encodeURIComponent(sku)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export function bajaProducto(sku) {
  return request(`/api/v1/productos/${encodeURIComponent(sku)}`, {
    method: 'DELETE',
  });
}
