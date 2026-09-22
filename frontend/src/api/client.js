/**
 * Cliente API centralizado — único punto con fetch.
 * RF-3, RF-4, RF-5. Lee solo import.meta.env.VITE_API_URL sin hardcode.
 */

export function validarUrlBase(url) {
  if (typeof url !== 'string') return false;
  const trimmed = url.trim();
  if (!trimmed) return false;
  try {
    const u = new URL(trimmed);
    return u.protocol === 'http:' || u.protocol === 'https:';
  } catch {
    return false;
  }
}

export function normalizarUrlBase(url) {
  return url.trim().replace(/\/+$/, '');
}

export function obtenerUrlBase() {
  const raw = import.meta.env?.VITE_API_URL;
  if (!validarUrlBase(raw ?? '')) return null;
  return normalizarUrlBase(raw);
}

export function esConfigValida() {
  return obtenerUrlBase() !== null;
}

const MENSAJE_CONEXION = 'Error de conexión con el servidor';
const MENSAJE_VALIDACION = 'No se pudo completar la solicitud. Revisa los datos e intenta nuevamente.';
const MENSAJE_SESION_EXPIRADA = 'Sesión expirada, inicia sesión nuevamente';
const TIMEOUT_MS = 10000;

let authTokenGetter = null;
let onUnauthorized = null;

export function setAuthTokenGetter(fn) {
  authTokenGetter = fn;
}

export function setOnUnauthorized(fn) {
  onUnauthorized = fn;
}

function esRutaLogin(ruta) {
  return ruta === '/api/v1/auth/login' || ruta.endsWith('/auth/login');
}

function construirUrl(ruta) {
  const base = obtenerUrlBase();
  if (!base) {
    throw { tipo: 'conexion', status: null, mensaje: MENSAJE_CONEXION, reintentable: true };
  }
  const rutaNorm = ruta.startsWith('/') ? ruta : `/${ruta}`;
  return `${base}${rutaNorm}`;
}

function extraerMensajeValidacion(json) {
  if (!json || typeof json !== 'object') return null;
  const candidatos = [json.detail, json.mensaje, json.message, json.error, json.msg, json.title];
  for (const c of candidatos) {
    if (typeof c === 'string' && c.trim()) return c.trim();
  }
  // si detail es array (FastAPI validation) — decisión 4h: primer mensaje legible
  if (Array.isArray(json.detail)) {
    const msgs = json.detail.map(d => d.msg || d.message).filter(Boolean);
    if (msgs.length) return msgs[0];
  }
  return null;
}

export async function request(ruta, opciones = {}) {
  const url = construirUrl(ruta);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  const esLogin = esRutaLogin(ruta);
  const token = !esLogin && authTokenGetter ? authTokenGetter() : null;

  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(opciones.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  try {
    const response = await fetch(url, {
      ...opciones,
      headers,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    // Intentar parsear JSON según content-type o siempre intentar
    let data = null;
    const contentType = response.headers?.get?.('content-type') || '';
    // intentar json siempre, pero tolerar vacío/no-json
    try {
      // 204 No Content no tiene body
      if (response.status === 204) {
        return null;
      }
      data = await response.json();
    } catch {
      // si no es JSON o vacío, data queda null
      try {
        const text = await response.text();
        data = text ? null : null;
      } catch {
        data = null;
      }
      // si no pudimos parsear y es error 4xx, usaremos genérico
      if (!response.ok && response.status >= 400 && response.status < 500) {
        throw { tipo: 'validacion', status: response.status, mensaje: MENSAJE_VALIDACION, reintentable: false };
      }
    }

    if (response.ok) {
      return data;
    }

    // 401 global con exclusión de login — RF-5
    if (response.status === 401 && !esRutaLogin(ruta)) {
      const tieneToken = !!token;
      if (tieneToken && onUnauthorized) {
        try {
          onUnauthorized();
        } catch {}
      }
      if (tieneToken) {
        throw { tipo: 'autenticacion', status: 401, mensaje: MENSAJE_SESION_EXPIRADA, reintentable: false };
      }
      // sin token, cae a validación normal (no hay sesión que limpiar)
    }

    // 4xx → validación (incluido 401 de login) sin reintento
    if (response.status >= 400 && response.status < 500) {
      const mensajeEspecifico = extraerMensajeValidacion(data);
      const mensaje = mensajeEspecifico || MENSAJE_VALIDACION;
      throw { tipo: 'validacion', status: response.status, mensaje, reintentable: false };
    }

    // 5xx → conexión con reintento
    if (response.status >= 500) {
      throw { tipo: 'conexion', status: response.status, mensaje: MENSAJE_CONEXION, reintentable: true };
    }

    // otros errores → conexión
    throw { tipo: 'conexion', status: response.status, mensaje: MENSAJE_CONEXION, reintentable: true };
  } catch (error) {
    clearTimeout(timeoutId);
    // si ya es nuestro error tipado, re-lanzar
    if (error && typeof error === 'object' && 'tipo' in error) {
      throw error;
    }
    // AbortError por timeout
    if (error && (error.name === 'AbortError' || error.message?.includes('aborted'))) {
      throw { tipo: 'conexion', status: null, mensaje: MENSAJE_CONEXION, reintentable: true };
    }
    // TypeError Failed to fetch, CORS, red
    if (error instanceof TypeError) {
      throw { tipo: 'conexion', status: null, mensaje: MENSAJE_CONEXION, reintentable: true };
    }
    // fallback
    throw { tipo: 'conexion', status: null, mensaje: MENSAJE_CONEXION, reintentable: true };
  }
}

export function get(ruta, opciones = {}) {
  return request(ruta, { ...opciones, method: 'GET' });
}

export function post(ruta, body, opciones = {}) {
  return request(ruta, { ...opciones, method: 'POST', body: JSON.stringify(body) });
}
