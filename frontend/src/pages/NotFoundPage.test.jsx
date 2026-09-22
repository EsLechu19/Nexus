import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import NotFoundPage from './NotFoundPage.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T14 — NotFoundPage — RF-2', () => {
  it('renderiza 404 con mensaje en español', () => {
    render(<NotFoundPage />);
    expect(screen.getByText(/404 — Página no encontrada/i)).toBeInTheDocument();
    expect(screen.getByText(/La ruta solicitada no existe/i)).toBeInTheDocument();
  });

  it('no contiene fetch', () => {
    const content = fs.readFileSync(path.join(__dirname, 'NotFoundPage.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });

  it('es accesible con heading', () => {
    render(<NotFoundPage />);
    expect(screen.getByRole('heading', { name: /404/i })).toBeInTheDocument();
  });
});
