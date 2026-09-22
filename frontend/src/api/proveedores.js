import { request } from './client.js';

/**
 * API de proveedores — RF-1..4
 * Usa cliente centralizado de 005 (request tipado).
 * No hace fetch directo (constitución §3).
 */

export function listarProveedores() {
  return request('/api/v1/proveedores', { method: 'GET' });
}

export function crearProveedor({ codigo, nombre, email, telefono, direccion }) {
  const body = { codigo, nombre };
  // opcional ausente (undefined) → omitido, null → null, "" → se envía tal cual (backend valida 422)
  if (email !== undefined) body.email = email;
  if (telefono !== undefined) body.telefono = telefono;
  if (direccion !== undefined) body.direccion = direccion;
  return request('/api/v1/proveedores', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function editarProveedor(codigo, { nombre, email, telefono, direccion } = {}) {
  const body = {};
  // solo campos con intención: null borra, ausente conserva, "" nunca se envía (bloqueo local)
  if (nombre !== undefined) {
    if (!(typeof nombre === 'string' && nombre.trim() === '')) {
      body.nombre = nombre;
    }
  }
  if (email !== undefined) {
    if (email === null) {
      body.email = null;
    } else if (!(typeof email === 'string' && email.trim() === '')) {
      body.email = email;
    }
  }
  if (telefono !== undefined) {
    if (telefono === null) {
      body.telefono = null;
    } else if (!(typeof telefono === 'string' && telefono.trim() === '')) {
      body.telefono = telefono;
    }
  }
  if (direccion !== undefined) {
    if (direccion === null) {
      body.direccion = null;
    } else if (!(typeof direccion === 'string' && direccion.trim() === '')) {
      body.direccion = direccion;
    }
  }
  // nunca enviar codigo ni estado, solo nombre/email/telefono/direccion
  return request(`/api/v1/proveedores/${encodeURIComponent(codigo)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export function bajaProveedor(codigo) {
  return request(`/api/v1/proveedores/${encodeURIComponent(codigo)}`, {
    method: 'DELETE',
  });
}
