import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ConfigErrorBanner from './ConfigErrorBanner.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T11 — ConfigErrorBanner — RF-4', () => {
  it('renderiza mensaje fijo y botón Reintentar con role alert', () => {
    const onReintentar = vi.fn();
    render(<ConfigErrorBanner mensaje="Error de conexión con el servidor" onReintentar={onReintentar} />);
    expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument();
    const btn = screen.getByRole('button', { name: /Reintentar/i });
    expect(btn).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('cuando cargando deshabilita botón', () => {
    render(<ConfigErrorBanner mensaje="Error de conexión con el servidor" cargando={true} />);
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeDisabled();
  });

  it('click Reintentar llama onReintentar sin reload', async () => {
    const onReintentar = vi.fn();
    render(<ConfigErrorBanner mensaje="Error de conexión con el servidor" onReintentar={onReintentar} />);
    await userEvent.click(screen.getByRole('button', { name: /Reintentar/i }));
    expect(onReintentar).toHaveBeenCalledTimes(1);
    // no debe usar window.location.reload (verificado por no contener reload)
    const content = fs.readFileSync(path.join(__dirname, 'ConfigErrorBanner.jsx'), 'utf8');
    expect(content).not.toMatch(/window\.location\.reload/);
    expect(content).not.toMatch(/reload\(\)/);
  });

  it('no contiene fetch', () => {
    const content = fs.readFileSync(path.join(__dirname, 'ConfigErrorBanner.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });

  it('es presentacional, mantiene nav visible (no suprime nav)', () => {
    // el banner solo es un div con alert, no incluye nav/main que pertenecen a AppLayout
    const { container } = render(<ConfigErrorBanner mensaje="Error de conexión con el servidor" />);
    expect(container.querySelector('nav')).not.toBeInTheDocument();
  });
});
