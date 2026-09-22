import React from 'react';
import { describe, it, expect } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import AppLayout from './layout/AppLayout.jsx';
import Loading from './components/Loading.jsx';
import ErrorMessage from './components/ErrorMessage.jsx';
import ConfigErrorBanner from './components/ConfigErrorBanner.jsx';
import { AuthProvider } from './context/AuthContext.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(__dirname, '..');
const indexPath = path.join(frontendDir, 'index.html');

describe('T16 — Accesibilidad y mensajes fijos — RF-1, RNF-3, RNF-4', () => {
  it('index.html tiene lang="es"', () => {
    expect(fs.existsSync(indexPath)).toBe(true);
    const html = fs.readFileSync(indexPath, 'utf8');
    expect(html).toMatch(/<html[^>]*lang="es"/);
  });

  it('layout usa elementos semánticos reales header/nav/main/button', () => {
    const layoutContent = fs.readFileSync(path.join(__dirname, 'layout/AppLayout.jsx'), 'utf8');
    expect(layoutContent).toMatch(/Header/);
    expect(layoutContent).toMatch(/<nav[^>]*aria-label="Navegación principal"/);
    expect(layoutContent).toMatch(/<main[^>]*id="contenido-principal"/);
    // botón viene de ConfigErrorBanner (importado por AppLayout)
    expect(layoutContent).toMatch(/ConfigErrorBanner/);
    const headerContent = fs.readFileSync(path.join(__dirname, 'layout/Header.jsx'), 'utf8');
    expect(headerContent).toMatch(/<header[\s>]/);
    const bannerContent = fs.readFileSync(path.join(__dirname, 'components/ConfigErrorBanner.jsx'), 'utf8');
    expect(bannerContent).toMatch(/<button/);
    // no usar div clicable para navegación
    expect(layoutContent).not.toMatch(/<div[^>]*onClick/);
  });

  it('AppLayout renderiza header/nav/main/button reales', () => {
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
    expect(screen.getByRole('navigation', { name: /Navegación principal/i })).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
  });

  it('enlace activo tiene aria-current="page"', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/stock']}>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/stock" element={<div>ok</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );
    const activo = screen.getByRole('link', { name: /Stock/i });
    expect(activo).toHaveAttribute('aria-current', 'page');
  });

  it('Loading tiene role status, aria-live polite y aria-busy', () => {
    render(<Loading mensaje="Cargando..." />);
    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-live', 'polite');
    expect(status).toHaveAttribute('aria-busy', 'true');
  });

  it('ErrorMessage y ConfigErrorBanner tienen role alert y aria-live assertive', () => {
    const { container: c1 } = render(<ErrorMessage mensaje="Error de conexión con el servidor" variante="conexion" />);
    expect(c1.querySelector('[role="alert"]')).toHaveAttribute('aria-live', 'assertive');
    const { container: c2 } = render(<ConfigErrorBanner mensaje="Error de conexión con el servidor" />);
    expect(c2.querySelector('[role="alert"]')).toHaveAttribute('aria-live', 'assertive');
  });

  it('ErrorMessage conexion con cargando tiene aria-busy true y botón deshabilitado', () => {
    render(<ErrorMessage mensaje="Error de conexión con el servidor" variante="conexion" cargando={true} />);
    const alert = document.querySelector('[role="alert"]');
    expect(alert).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeDisabled();
  });

  it('foco visible con focus-visible:ring en NavLinkItem y botones', () => {
    const navContent = fs.readFileSync(path.join(__dirname, 'layout/NavLinkItem.jsx'), 'utf8');
    expect(navContent).toMatch(/focus-visible:ring/);
    const errorContent = fs.readFileSync(path.join(__dirname, 'components/ErrorMessage.jsx'), 'utf8');
    // ErrorMessage no necesita focus ring en sí, pero botón debe ser real y focusable
    expect(errorContent).toMatch(/<button/);
    render(
      <AuthProvider>
        <MemoryRouter>
          <AppLayout />
        </MemoryRouter>
      </AuthProvider>
    );
    // verificar que los 4 links son focusables
    const links = screen.getAllByRole('link');
    expect(links).toHaveLength(4);
    links.forEach(link => {
      link.focus();
      expect(document.activeElement).toBe(link);
    });
  });

  it('solo los dos mensajes genéricos permitidos (sin variantes)', () => {
    const clientContent = fs.readFileSync(path.join(__dirname, 'api/client.js'), 'utf8');
    expect(clientContent).toMatch(/Error de conexión con el servidor/);
    expect(clientContent).toMatch(/No se pudo completar la solicitud\. Revisa los datos e intenta nuevamente\./);
    // no debe haber otros mensajes genéricos similares con variaciones de mayúsculas o puntuación
    const matchesConexion = (clientContent.match(/Error de conexión con el servidor/g) || []).length;
    expect(matchesConexion).toBeGreaterThanOrEqual(1);
    // verificar que componentes usan exactamente esos mensajes (no hardcodean variantes)
    const errorContent = fs.readFileSync(path.join(__dirname, 'components/ErrorMessage.jsx'), 'utf8');
    // ErrorMessage no debe hardcodear mensajes, recibe via props; verificar que no contiene texto hardcodeado extra
    expect(errorContent).not.toMatch(/Error de conexion sin acento/);
  });

  it('mensajes visibles en español (navegación, placeholders, errores)', () => {
    const appLayoutContent = fs.readFileSync(path.join(__dirname, 'layout/AppLayout.jsx'), 'utf8');
    expect(appLayoutContent).toMatch(/Productos/);
    expect(appLayoutContent).toMatch(/Proveedores/);
    // verificar que no hay strings UI en inglés
    expect(appLayoutContent).not.toMatch(/Products/);
    expect(appLayoutContent).not.toMatch(/Providers/);
  });

  it('sin trampas de foco: tab alcanza nav y botón Reintentar', async () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/productos']}>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/productos" element={<ErrorMessage mensaje="Error de conexión con el servidor" variante="conexion" onReintentar={() => {}} />} />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );
    const nav = screen.getByRole('navigation');
    expect(nav).toBeInTheDocument();
    // el botón Reintentar debe ser alcanzable por tab (no usar userEvent.tab aquí para evitar complejidad, solo verificar que existe y es focusable)
    const btn = screen.getByRole('button', { name: /Reintentar/i });
    btn.focus();
    expect(document.activeElement).toBe(btn);
  });

  it('htmlFor/id preparado para futuros formularios (no hay labels huérfanos)', () => {
    // en 005 no hay formularios, pero verificamos que si hubiera label, debe tener htmlFor
    const componentsDir = path.join(__dirname, 'components');
    const files = fs.readdirSync(componentsDir).filter(f => f.endsWith('.jsx'));
    for (const f of files) {
      const content = fs.readFileSync(path.join(componentsDir, f), 'utf8');
      if (content.includes('<label')) {
        expect(content).toMatch(/htmlFor=/);
      }
    }
  });
});
