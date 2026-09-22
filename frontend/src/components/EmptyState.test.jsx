import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import EmptyState from './EmptyState.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T09 — EmptyState — RF-5', () => {
  it('renderiza por defecto "Sin datos disponibles" sin botón', () => {
    render(<EmptyState />);
    expect(screen.getByText('Sin datos disponibles')).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('permite mensaje y descripción personalizados', () => {
    render(<EmptyState mensaje="Sin productos" descripcion="No hay productos aún" />);
    expect(screen.getByText('Sin productos')).toBeInTheDocument();
    expect(screen.getByText('No hay productos aún')).toBeInTheDocument();
  });

  it('diferenciado de loading/error (sin role alert/status de error)', () => {
    const { container } = render(<EmptyState />);
    expect(container.querySelector('[role="alert"]')).not.toBeInTheDocument();
  });

  it('no contiene fetch', () => {
    const content = fs.readFileSync(path.join(__dirname, 'EmptyState.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });
});
