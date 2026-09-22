import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import AppLayout from './AppLayout.jsx';
import NavLinkItem from './NavLinkItem.jsx';
import { AuthProvider } from '../context/AuthContext.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T03 — AppLayout y NavLinkItem — RF-1', () => {
  it('renderiza header, nav con aria-label y 4 enlaces, y main con id', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/productos']}>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/productos" element={<div>contenido</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );
    expect(screen.getByRole('banner')).toBeInTheDocument(); // header
    const nav = screen.getByRole('navigation', { name: /Navegación principal/i });
    expect(nav).toBeInTheDocument();
    expect(nav.tagName).toBe('NAV');
    const links = screen.getAllByRole('link');
    expect(links).toHaveLength(4);
    expect(links[0]).toHaveTextContent(/Productos/i);
    expect(links[1]).toHaveTextContent(/Proveedores/i);
    expect(links[2]).toHaveTextContent(/Movimientos/i);
    expect(links[3]).toHaveTextContent(/Stock/i);
    expect(links[0].getAttribute('href')).toBe('/productos');
    expect(links[1].getAttribute('href')).toBe('/proveedores');
    expect(links[2].getAttribute('href')).toBe('/movimientos');
    expect(links[3].getAttribute('href')).toBe('/stock');
    const main = screen.getByRole('main');
    expect(main).toHaveAttribute('id', 'contenido-principal');
    expect(screen.getByText('contenido')).toBeInTheDocument(); // Outlet funciona
  });

  it('marca enlace activo con aria-current="page" y clase focus-visible:ring', async () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/proveedores']}>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/proveedores" element={<div>ok</div>} />
              <Route path="/productos" element={<div>prod</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );
    const activo = screen.getByRole('link', { name: /Proveedores/i });
    expect(activo).toHaveAttribute('aria-current', 'page');
    // NavLinkItem debe aplicar focus-visible:ring
    expect(activo.className).toMatch(/focus-visible:ring/);
    const inactivo = screen.getByRole('link', { name: /Productos/i });
    expect(inactivo).not.toHaveAttribute('aria-current');
  });

  it('NavLinkItem es un link accesible por teclado (focus visible)', () => {
    render(
      <MemoryRouter>
        <NavLinkItem to="/stock">Stock</NavLinkItem>
      </MemoryRouter>
    );
    const link = screen.getByRole('link', { name: /Stock/i });
    expect(link).toHaveAttribute('href', '/stock');
    link.focus();
    expect(document.activeElement).toBe(link);
  });

  it('layout no contiene fetch (constitución §3)', () => {
    const layoutDir = __dirname;
    const files = fs.readdirSync(layoutDir).filter(f => f.endsWith('.jsx') && !f.includes('.test.'));
    for (const f of files) {
      const content = fs.readFileSync(path.join(layoutDir, f), 'utf8');
      expect(content).not.toMatch(/fetch\s*\(/);
      expect(content).not.toMatch(/import.*fetch/);
    }
  });

  it('mantiene navegación visible al cambiar de ruta (sin recargar layout)', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/productos']}>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/productos" element={<div>prod</div>} />
              <Route path="/stock" element={<div>stock</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );
    // nav y main visibles en primera ruta
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
    expect(screen.getByText('prod')).toBeInTheDocument();
    // el layout no recarga: el header permanece
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });
});
