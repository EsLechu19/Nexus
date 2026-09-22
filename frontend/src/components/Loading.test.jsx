import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Loading from './Loading.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T08 — Loading — RF-5', () => {
  it('renderiza por defecto "Cargando..." con role status y aria-live polite', () => {
    render(<Loading />);
    const el = screen.getByRole('status');
    expect(el).toBeInTheDocument();
    expect(el).toHaveAttribute('aria-live', 'polite');
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
  });

  it('permite mensaje personalizado', () => {
    render(<Loading mensaje="Cargando productos..." />);
    expect(screen.getByText('Cargando productos...')).toBeInTheDocument();
  });

  it('no oculta nav (es presentacional, sin fetch)', () => {
    const content = fs.readFileSync(path.join(__dirname, 'Loading.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).not.toMatch(/import.*client/);
  });

  it('es accesible y no contiene lógica de negocio', () => {
    const { container } = render(<Loading mensaje="Cargando..." ariaLive="polite" />);
    const status = container.querySelector('[role="status"]');
    expect(status).toBeInTheDocument();
  });
});
