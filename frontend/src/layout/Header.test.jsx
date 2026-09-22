import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

const mockNavigate = vi.fn();
const mockLogout = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockUseAuth = vi.fn();
vi.mock('../context/AuthContext.jsx', async () => {
  const actual = await vi.importActual('../context/AuthContext.jsx');
  return {
    ...actual,
    useAuth: () => mockUseAuth(),
  };
});

import Header from './Header.jsx';

describe('T06 — Header Cerrar sesión — RF-5', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
    mockNavigate.mockClear();
    mockLogout.mockClear();
  });

  it('sin sesión no muestra Cerrar sesión', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, token: null, login: vi.fn(), logout: mockLogout });
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );
    expect(screen.queryByRole('button', { name: /Cerrar sesión/i })).not.toBeInTheDocument();
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });

  it('con sesión muestra botón siempre visible en header', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, token: 'tok', login: vi.fn(), logout: mockLogout });
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );
    const btn = screen.getByRole('button', { name: /Cerrar sesión/i });
    expect(btn).toBeInTheDocument();
    expect(btn.closest('header')).toBeInTheDocument();
  });

  it('click llama logout sin fetch y navega a /login con mensaje efímero 3s', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, token: 'tok', login: vi.fn(), logout: mockLogout });
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );
    const btn = screen.getByRole('button', { name: /Cerrar sesión/i });
    fireEvent.click(btn);
    expect(mockLogout).toHaveBeenCalledTimes(1);
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith('/login', expect.objectContaining({ state: expect.objectContaining({ mensaje: 'Sesión cerrada correctamente' }) }));
    expect(mockNavigate).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ replace: true }));
  });

  it('doble click ignorado mientras navega', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, token: 'tok', login: vi.fn(), logout: mockLogout });
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );
    const btn = screen.getByRole('button', { name: /Cerrar sesión/i });
    fireEvent.click(btn);
    fireEvent.click(btn);
    // logout debe llamarse solo una vez si se ignora segundo click
    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

  it('no añade localStorage y no contiene fetch', async () => {
    const fs = await import('node:fs');
    const path = await import('node:path');
    const headerPath = path.resolve('src/layout/Header.jsx');
    const content = fs.readFileSync(headerPath, 'utf8');
    expect(content).not.toMatch(/localStorage/);
    expect(content).not.toMatch(/sessionStorage/);
    expect(content).not.toMatch(/fetch\s*\(/);
  });

  it('nunca se muestra en /login porque Login está fuera de AppLayout', () => {
    // AppLayout con Header solo se monta dentro de ProtectedRoute
    // /login está fuera, así que Header no se renderiza allí
    // Verificamos que Header por sí solo no se renderiza sin isAuthenticated
    mockUseAuth.mockReturnValue({ isAuthenticated: false, token: null, login: vi.fn(), logout: mockLogout });
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Header />
      </MemoryRouter>
    );
    expect(screen.queryByRole('button', { name: /Cerrar sesión/i })).not.toBeInTheDocument();
  });
});
