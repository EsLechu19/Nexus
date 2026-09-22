import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App.jsx';

vi.mock('./context/AuthContext.jsx', async () => {
  const actual = await vi.importActual('./context/AuthContext.jsx');
  return {
    ...actual,
    useAuth: () => ({ isAuthenticated: true, token: 'test-token', login: vi.fn(), logout: vi.fn() }),
  };
});

describe('T04 — App.jsx ruteo — RF-1, RF-2', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [], headers: { get: () => 'application/json' } }));
  });

  it('redirige / a /productos', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    // debe mostrar Productos page tras redirección (no placeholder)
    expect(await screen.findByText(/Crear producto/i)).toBeInTheDocument();
    // nav y header siguen visibles (AppLayout)
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });

  it('ruta /productos muestra Productos page', async () => {
    render(
      <MemoryRouter initialEntries={['/productos']}>
        <App />
      </MemoryRouter>
    );
    expect(await screen.findByText(/Crear producto/i)).toBeInTheDocument();
  });

  it('ruta /proveedores muestra Proveedores page', async () => {
    render(
      <MemoryRouter initialEntries={['/proveedores']}>
        <App />
      </MemoryRouter>
    );
    // 007 T08: /proveedores ya no es placeholder, muestra listado de proveedores
    expect(await screen.findByRole('heading', { name: /Proveedores/i })).toBeInTheDocument();
    expect(screen.queryByText(/Proveedores — En construcción/i)).not.toBeInTheDocument();
  });

  it('ruta /movimientos muestra Movimientos page', async () => {
    render(
      <MemoryRouter initialEntries={['/movimientos']}>
        <App />
      </MemoryRouter>
    );
    // 008 T07: /movimientos ya no es placeholder, muestra historial de movimientos
    expect(await screen.findByRole('heading', { name: /Movimientos/i })).toBeInTheDocument();
    expect(screen.queryByText(/Movimientos — En construcción/i)).not.toBeInTheDocument();
  });

  it('ruta /stock muestra Stock page', async () => {
    render(
      <MemoryRouter initialEntries={['/stock']}>
        <App />
      </MemoryRouter>
    );
    // 009 T05: /stock ya no es placeholder, muestra consulta de stock
    expect(await screen.findByRole('heading', { name: /Stock/i })).toBeInTheDocument();
    expect(screen.queryByText(/Stock — En construcción/i)).not.toBeInTheDocument();
  });

  it('ruta inexistente muestra 404 NotFoundPage', () => {
    render(
      <MemoryRouter initialEntries={['/ruta-inexistente']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByText(/Página no encontrada/i)).toBeInTheDocument();
    // mantiene layout
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
  });

  it('todo está anidado bajo AppLayout (nav y main persistentes)', () => {
    render(
      <MemoryRouter initialEntries={['/productos']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByRole('navigation', { name: /Navegación principal/i })).toBeInTheDocument();
    expect(screen.getByRole('main')).toHaveAttribute('id', 'contenido-principal');
    expect(screen.getAllByRole('link')).toHaveLength(4);
  });

  it('navegación no recarga layout (header persiste)', async () => {
    render(
      <MemoryRouter initialEntries={['/productos']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByRole('banner')).toBeInTheDocument();
    expect(await screen.findByText(/Crear producto/i)).toBeInTheDocument();
  });
});
