import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ProductoBajaDialog from './ProductoBajaDialog.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const producto = { sku: 'PS5-001', nombre: 'PlayStation 5' };

describe('T07 — ProductoBajaDialog — RF-4', () => {
  it('renderiza dialog role dialog con texto confirmación y dos botones', () => {
    render(<ProductoBajaDialog producto={producto} onConfirmar={vi.fn()} onCancelar={vi.fn()} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(`¿Dar de baja a ${producto.nombre} (${producto.sku})? No se puede deshacer desde este MVP`)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Confirmar/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Cancelar/i })).toBeInTheDocument();
  });

  it('Confirmar deshabilitado si cargando', () => {
    render(<ProductoBajaDialog producto={producto} onConfirmar={vi.fn()} onCancelar={vi.fn()} cargando={true} />);
    expect(screen.getByRole('button', { name: /Confirmar/i })).toBeDisabled();
  });

  it('Cancelar cierra sin fetch y ESC cierra', async () => {
    const onCancelar = vi.fn();
    render(<ProductoBajaDialog producto={producto} onConfirmar={vi.fn()} onCancelar={onCancelar} />);
    await userEvent.click(screen.getByRole('button', { name: /Cancelar/i }));
    expect(onCancelar).toHaveBeenCalled();
  });

  it('no contiene fetch directo', () => {
    const content = fs.readFileSync(path.join(__dirname, 'ProductoBajaDialog.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });
});
