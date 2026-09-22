import { post } from './client.js';

/**
 * Wrapper de autenticación — RF-2.
 * Aplica trim a email, nunca añade Bearer (delegado a client.js que excluye /auth/login),
 * no guarda token (lo devuelve al contexto), y propaga 422 tal cual.
 */
export async function login({ email, password }) {
  const emailTrim = typeof email === 'string' ? email.trim() : email;
  return post('/api/v1/auth/login', { email: emailTrim, password });
}
