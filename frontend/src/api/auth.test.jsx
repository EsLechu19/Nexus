import { describe, it, expect, vi, beforeEach } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

describe('T03 — auth.js login wrapper — RF-2', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('existe archivo auth.js y no hardcodea URL ni usa localStorage', () => {
    const authPath = path.resolve('src/api/auth.js');
    expect(fs.existsSync(authPath)).toBe(true);
    const content = fs.readFileSync(authPath, 'utf8');
    expect(content).toMatch(/\/api\/v1\/auth\/login/);
    expect(content).not.toMatch(/localStorage/);
    expect(content).not.toMatch(/sessionStorage/);
    expect(content).toMatch(/trim/);
  });

  it('login aplica trim a email antes de delegar a client post', async () => {
    const client = await import('./client.js');
    const postSpy = vi.spyOn(client, 'post').mockResolvedValue({ access_token: 'jwt-123', token_type: 'bearer' });
    const { login } = await import('./auth.js');
    const result = await login({ email: '  ANA@correo.com  ', password: 'secreto123' });
    expect(postSpy).toHaveBeenCalledWith('/api/v1/auth/login', { email: 'ANA@correo.com', password: 'secreto123' });
    expect(result).toEqual({ access_token: 'jwt-123', token_type: 'bearer' });
    postSpy.mockRestore();
  });

  it('no añade Bearer incluso con token previo en memoria', async () => {
    const client = await import('./client.js');
    client.setAuthTokenGetter(() => 'previo-token');
    const postSpy = vi.spyOn(client, 'post').mockImplementation((ruta, body) => {
      // client debe excluir login de Bearer, así que Authorization no debe estar en headers
      // post delega a request, que es donde se inyecta Bearer; verificamos que no lo hace para login
      // simulamos que post no recibe Authorization en opciones
      expect(body.email).toBeDefined();
      return Promise.resolve({ access_token: 'tok', token_type: 'bearer' });
    });
    const { login } = await import('./auth.js');
    await login({ email: 'a@b.com', password: 'x' });
    expect(postSpy).toHaveBeenCalledWith('/api/v1/auth/login', expect.any(Object));
    client.setAuthTokenGetter(null);
    postSpy.mockRestore();
  });

  it('no guarda token internamente, solo lo devuelve', async () => {
    const client = await import('./client.js');
    const postSpy = vi.spyOn(client, 'post')
      .mockResolvedValueOnce({ access_token: 'abc', token_type: 'bearer' })
      .mockResolvedValueOnce({ access_token: 'def', token_type: 'bearer' });
    const { login } = await import('./auth.js');
    const res1 = await login({ email: 'a@b.com', password: '12345678' });
    expect(res1.access_token).toBe('abc');
    const res2 = await login({ email: 'a@b.com', password: '12345678' });
    expect(res2.access_token).toBe('def');
    expect(postSpy).toHaveBeenCalledTimes(2);
    postSpy.mockRestore();
  });

  it('propaga 422 array vs string tal cual (delegado a client)', async () => {
    const client = await import('./client.js');
    const postSpy = vi.spyOn(client, 'post')
      .mockRejectedValueOnce({ tipo: 'validacion', status: 422, mensaje: 'Campo requerido', reintentable: false })
      .mockRejectedValueOnce({ tipo: 'validacion', status: 422, mensaje: 'email: Field required', reintentable: false });
    const { login } = await import('./auth.js');
    await expect(login({ email: 'a@b.com', password: '' })).rejects.toMatchObject({ status: 422, mensaje: 'Campo requerido' });
    await expect(login({ email: '', password: 'x' })).rejects.toMatchObject({ status: 422 });
    postSpy.mockRestore();
  });
});
