import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

const mockNavigate = vi.fn();
const mockLogin = vi.fn();

// Mock de AuthContext
vi.mock('../context/AuthContext.jsx', async () => {
  const actual = await vi.importActual('../context/AuthContext.jsx');
  return {
    ...actual,
    useAuth: () => ({
      token: null,
      isAuthenticated: false,
      login: mockLogin,
      logout: vi.fn(),
    }),
  };
});

// Mock de react-router navigate
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

function renderLogin(initialEntries = ['/login'], state = null) {
  // Login no necesita ruta protegida, se renderiza directo
  const entry = state ? { pathname: '/login', state } : '/login';
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/productos" element={<div>Productos</div>} />
      </Routes>
    </MemoryRouter>
  );
}

import Login from './Login.jsx';

describe('T04 — Login.jsx — RF-1, RF-2', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockNavigate.mockClear();
    mockLogin.mockClear();
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
    vi.stubGlobal('fetch', vi.fn());
  });

  it('muestra formulario con email, contraseña y botón, sin registro/recuperación', () => {
    renderLogin();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Iniciar sesión/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toHaveAttribute('autocomplete', 'email');
    expect(screen.getByLabelText(/contraseña/i)).toHaveAttribute('autocomplete', 'current-password');
    expect(screen.queryByText(/registro/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/recuperar/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/rol/i)).not.toBeInTheDocument();
  });

  it('validación local Campo requerido si vacío, sin llamar a fetch', async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
    renderLogin();
    fireEvent.click(screen.getByRole('button', { name: /Iniciar sesión/i }));
    expect(await screen.findAllByText('Campo requerido')).toHaveLength(2);
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('permite envío con email no vacío y hace trim antes de fetch', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ access_token: 'tok', token_type: 'bearer' }),
      headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', fetchMock);
    renderLogin();
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: '  ANA@correo.com  ' } });
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'secreto123' } });
    fireEvent.click(screen.getByRole('button', { name: /Iniciar sesión/i }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toContain('/api/v1/auth/login');
    const body = JSON.parse(opts.body);
    expect(body.email).toBe('ANA@correo.com');
    expect(body.password).toBe('secreto123');
    // no debe adjuntar Bearer aunque haya token previo
    expect(opts.headers.Authorization).toBeUndefined();
  });

  it('mientras fetch pendiente deshabilita inputs+botón con spinner e ignora dobles clics', async () => {
    let resolveFetch;
    const fetchMock = vi.fn().mockImplementation(() => new Promise((res) => { resolveFetch = res; }));
    vi.stubGlobal('fetch', fetchMock);
    renderLogin();
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'x' } });
    fireEvent.click(screen.getByRole('button', { name: /Iniciar sesión/i }));
    // segundo clic debe ser ignorado — el botón ya está en estado Cargando y deshabilitado
    // no intentamos hacer click de nuevo sobre "Iniciar sesión" porque ya no existe, verificamos que sigue deshabilitado
    expect(screen.getByLabelText(/email/i)).toBeDisabled();
    expect(screen.getByLabelText(/contraseña/i)).toBeDisabled();
    expect(screen.getByRole('button', { name: /Cargando/i })).toBeDisabled();
    expect(screen.getByText(/Cargando/i)).toBeInTheDocument();
    // debe haber solo una llamada
    expect(fetchMock).toHaveBeenCalledTimes(1);
    // resolver para limpiar
    resolveFetch({ ok: true, status: 200, json: async () => ({ access_token: 'tok', token_type: 'bearer' }), headers: { get: () => 'application/json' } });
    await waitFor(() => expect(screen.getByLabelText(/email/i)).not.toBeDisabled());
  });

  it('401 Credenciales inválidas sin guardar token y sin interceptor global', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Credenciales inválidas' }),
      headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', fetchMock);
    renderLogin();
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: /Iniciar sesión/i }));
    expect(await screen.findByText('Credenciales inválidas')).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('422 array muestra primer mensaje legible, string tal cual', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: async () => ({ detail: [{ msg: 'email: Field required' }, { msg: 'otro' }] }),
        headers: { get: () => 'application/json' },
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: async () => ({ detail: 'Error específico' }),
        headers: { get: () => 'application/json' },
      });
    vi.stubGlobal('fetch', fetchMock);
    renderLogin();
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'x' } });
    fireEvent.click(screen.getByRole('button', { name: /Iniciar sesión/i }));
    expect(await screen.findByText('email: Field required')).toBeInTheDocument();
    // segunda llamada
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'y' } });
    fireEvent.click(screen.getByRole('button', { name: /Iniciar sesión/i }));
    expect(await screen.findByText('Error específico')).toBeInTheDocument();
  });

  it('red/timeout muestra Error de conexión con Reintentar que reejecuta', async () => {
    const fetchMock = vi.fn()
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ access_token: 'tok', token_type: 'bearer' }),
        headers: { get: () => 'application/json' },
      });
    vi.stubGlobal('fetch', fetchMock);
    renderLogin();
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'x' } });
    fireEvent.click(screen.getByRole('button', { name: /Iniciar sesión/i }));
    expect(await screen.findByText('Error de conexión con el servidor')).toBeInTheDocument();
    const retryBtn = screen.getByRole('button', { name: /Reintentar/i });
    expect(retryBtn).toBeInTheDocument();
    fireEvent.click(retryBtn);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  });

  it('éxito guarda token y navega a from o /productos', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ access_token: 'jwt-ok', token_type: 'bearer' }),
      headers: { get: () => 'application/json' },
    });
    vi.stubGlobal('fetch', fetchMock);
    // con from
    const { unmount } = render(
      <MemoryRouter initialEntries={[{ pathname: '/login', state: { from: { pathname: '/stock' } } }]}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/stock" element={<div>Stock</div>} />
          <Route path="/productos" element={<div>Productos</div>} />
        </Routes>
      </MemoryRouter>
    );
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'x' } });
    fireEvent.click(screen.getByRole('button', { name: /Iniciar sesión/i }));
    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith('jwt-ok'));
    expect(mockNavigate).toHaveBeenCalledWith('/stock', expect.any(Object));
    unmount();
    mockLogin.mockClear();
    mockNavigate.mockClear();
    // sin from → /productos
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/productos" element={<div>Productos</div>} />
        </Routes>
      </MemoryRouter>
    );
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@b.com' } });
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'x' } });
    vi.stubGlobal('fetch', fetchMock);
    fireEvent.click(screen.getByRole('button', { name: /Iniciar sesión/i }));
    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith('jwt-ok'));
    expect(mockNavigate).toHaveBeenCalledWith('/productos', expect.any(Object));
  });
});
