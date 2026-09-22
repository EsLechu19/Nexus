import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

const mockUseAuth = vi.fn();
vi.mock('../context/AuthContext.jsx', async () => {
  const actual = await vi.importActual('../context/AuthContext.jsx');
  return {
    ...actual,
    useAuth: () => mockUseAuth(),
  };
});

import ProtectedRoute from './ProtectedRoute.jsx';
import Login from '../pages/Login.jsx';

describe('T05 — ProtectedRoute guard — RF-3', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  });

  it('sin token redirige a /login recordando ruta intentada sin fetch', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, token: null, login: vi.fn(), logout: vi.fn() });
    render(
      <MemoryRouter initialEntries={['/productos']}>
        <Routes>
          <Route path="/login" element={<div>Login</div>} />
          <Route element={<ProtectedRoute />}>
            <Route path="/productos" element={<div>Productos</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.queryByText('Productos')).not.toBeInTheDocument();
  });

  it('sin token y ruta inexistente va a /login no a 404 (guard primero)', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, token: null, login: vi.fn(), logout: vi.fn() });
    render(
      <MemoryRouter initialEntries={['/ruta-inexistente']}>
        <Routes>
          <Route path="/login" element={<div>Login</div>} />
          <Route element={<ProtectedRoute />}>
            <Route path="/productos" element={<div>Productos</div>} />
            <Route path="*" element={<div>404</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.queryByText('404')).not.toBeInTheDocument();
  });

  it('con token y ruta /login redirige a /productos (Login verifica)', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, token: 'tok', login: vi.fn(), logout: vi.fn() });
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/productos" element={<div>Productos</div>} />
        </Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText('Productos')).toBeInTheDocument();
  });

  it('con token permite acceso a ruta protegida y renderiza Outlet', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, token: 'tok', login: vi.fn(), logout: vi.fn() });
    render(
      <MemoryRouter initialEntries={['/productos']}>
        <Routes>
          <Route path="/login" element={<div>Login</div>} />
          <Route element={<ProtectedRoute />}>
            <Route path="/productos" element={<div>Productos</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Productos')).toBeInTheDocument();
    expect(screen.queryByText('Login')).not.toBeInTheDocument();
  });

  it('con token y ruta inexistente muestra 404', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, token: 'tok', login: vi.fn(), logout: vi.fn() });
    render(
      <MemoryRouter initialEntries={['/ruta-inexistente']}>
        <Routes>
          <Route path="/login" element={<div>Login</div>} />
          <Route element={<ProtectedRoute />}>
            <Route path="/productos" element={<div>Productos</div>} />
            <Route path="*" element={<div>404</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('404')).toBeInTheDocument();
  });

  it('F5 con token perdido vuelve a /login recordando ruta', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, token: null, login: vi.fn(), logout: vi.fn() });
    render(
      <MemoryRouter initialEntries={['/stock']}>
        <Routes>
          <Route path="/login" element={<div>Login</div>} />
          <Route element={<ProtectedRoute />}>
            <Route path="/stock" element={<div>Stock</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Login')).toBeInTheDocument();
  });
});
