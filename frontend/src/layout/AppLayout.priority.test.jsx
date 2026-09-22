import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

// Mock del cliente API para controlar config inválida
vi.mock('../api/client.js', () => ({
  validarUrlBase: vi.fn(() => false),
  normalizarUrlBase: vi.fn((u) => u.trim().replace(/\/+$/, '')),
  obtenerUrlBase: vi.fn(() => null),
  esConfigValida: vi.fn(() => false),
  request: vi.fn(),
  get: vi.fn(),
  post: vi.fn(),
  setAuthTokenGetter: vi.fn(),
  setOnUnauthorized: vi.fn(),
}));

import AppLayout from './AppLayout.jsx';
import PlaceholderPage from '../pages/PlaceholderPage.jsx';
import NotFoundPage from '../pages/NotFoundPage.jsx';
import { AuthProvider } from '../context/AuthContext.jsx';

describe('T15 — Prioridad error global — RF-2, RF-4', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('con banner global activo no renderiza placeholder (prioriza global sobre placeholder)', async () => {
    // AppLayout con mock esConfigValida=false debe mostrar banner y suprimir Outlet
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/productos']}>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/productos" element={<PlaceholderPage nombreSeccion="Productos" />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );
    expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeInTheDocument();
    // placeholder no debe estar visible cuando hay error global
    expect(screen.queryByText('Productos — En construcción')).not.toBeInTheDocument();
    // nav y header siguen visibles
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByRole('banner')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
  });

  it('con banner global activo no renderiza 404 (prioriza global sobre NotFound)', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/ruta-inexistente']}>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/productos" element={<PlaceholderPage nombreSeccion="Productos" />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );
    expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument();
    expect(screen.queryByText(/404 — Página no encontrada/i)).not.toBeInTheDocument();
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });

  it('fallo aislado por sección no escala a global (verificado por no usar fetch en layout)', async () => {
    // AppLayout no debe contener fetch ni escalar errores de sección
    const fs = await import('node:fs');
    const path = await import('node:path');
    const { fileURLToPath } = await import('node:url');
    const __dirname = path.dirname(fileURLToPath(import.meta.url));
    const content = fs.readFileSync(path.join(__dirname, 'AppLayout.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
    // el banner solo depende de esConfigValida, no de errores de sección
    expect(content).toMatch(/esConfigValida|obtenerUrlBase|ConfigErrorBanner/);
  });
});
