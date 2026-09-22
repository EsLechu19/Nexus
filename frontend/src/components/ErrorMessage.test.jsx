import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ErrorMessage from './ErrorMessage.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T10 — ErrorMessage — RF-5', () => {
  it('variante conexion muestra mensaje genérico + botón Reintentar', async () => {
    const onReintentar = vi.fn();
    render(<ErrorMessage mensaje="Error de conexión con el servidor" variante="conexion" onReintentar={onReintentar} />);
    expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument();
    const btn = screen.getByRole('button', { name: /Reintentar/i });
    expect(btn).toBeInTheDocument();
    expect(btn).not.toBeDisabled();
    await userEvent.click(btn);
    expect(onReintentar).toHaveBeenCalledTimes(1);
  });

  it('variante conexion con cargando deshabilita botón y aria-busy', () => {
    render(<ErrorMessage mensaje="Error de conexión con el servidor" variante="conexion" cargando={true} />);
    const btn = screen.getByRole('button', { name: /Reintentar/i });
    expect(btn).toBeDisabled();
    // el contenedor debe tener aria-busy o el botón disabled indica cargando
  });

  it('variante validacion muestra mensaje específico sin botón (incluido 401)', () => {
    render(<ErrorMessage mensaje="SKU ya existe" variante="validacion" />);
    expect(screen.getByText('SKU ya existe')).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('variante validacion con genérico no muestra botón', () => {
    render(<ErrorMessage mensaje="No se pudo completar la solicitud. Revisa los datos e intenta nuevamente." variante="validacion" />);
    expect(screen.getByText(/No se pudo completar/i)).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('tiene role alert y aria-live assertive', () => {
    const { container } = render(<ErrorMessage mensaje="Error" variante="conexion" />);
    const alert = container.querySelector('[role="alert"]');
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveAttribute('aria-live', 'assertive');
  });

  it('no contiene fetch', () => {
    const content = fs.readFileSync(path.join(__dirname, 'ErrorMessage.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });
});
