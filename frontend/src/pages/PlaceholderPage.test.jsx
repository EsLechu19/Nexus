import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import PlaceholderPage from './PlaceholderPage.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T13 — PlaceholderPage — RF-2', () => {
  it('renderiza "<Sección> — En construcción" con nombre de sección', () => {
    render(<PlaceholderPage nombreSeccion="Productos" />);
    expect(screen.getByText('Productos — En construcción')).toBeInTheDocument();
  });

  it('renderiza para cada sección con mensaje en español', () => {
    const { rerender } = render(<PlaceholderPage nombreSeccion="Proveedores" />);
    expect(screen.getByText('Proveedores — En construcción')).toBeInTheDocument();
    rerender(<PlaceholderPage nombreSeccion="Movimientos" />);
    expect(screen.getByText('Movimientos — En construcción')).toBeInTheDocument();
    rerender(<PlaceholderPage nombreSeccion="Stock" />);
    expect(screen.getByText('Stock — En construcción')).toBeInTheDocument();
  });

  it('no contiene fetch ni lógica de negocio', () => {
    const content = fs.readFileSync(path.join(__dirname, 'PlaceholderPage.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).not.toMatch(/useApiStatus/);
  });

  it('es presentacional y accesible (heading)', () => {
    render(<PlaceholderPage nombreSeccion="Productos" />);
    expect(screen.getByRole('heading', { name: /Productos — En construcción/i })).toBeInTheDocument();
  });
});
