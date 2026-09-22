import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ProveedorBajaDialog from './ProveedorBajaDialog.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const proveedor = { codigo: 'PROV-001', nombre: 'Central' };

describe('T07 — ProveedorBajaDialog — RF-4', () => {
  it('renderiza dialog role dialog con texto confirmación y dos botones', () => {
    render(<ProveedorBajaDialog proveedor={proveedor} onConfirmar={vi.fn()} onCancelar={vi.fn()} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(`¿Dar de baja a ${proveedor.nombre} (${proveedor.codigo})? No se puede deshacer desde este MVP`)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Confirmar/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Cancelar/i })).toBeInTheDocument();
  });

  it('Confirmar deshabilitado si cargando', () => {
    render(<ProveedorBajaDialog proveedor={proveedor} onConfirmar={vi.fn()} onCancelar={vi.fn()} cargando={true} />);
    expect(screen.getByRole('button', { name: /Confirmar/i })).toBeDisabled();
  });

  it('Cancelar cierra sin fetch y ESC cierra', async () => {
    const onCancelar = vi.fn();
    render(<ProveedorBajaDialog proveedor={proveedor} onConfirmar={vi.fn()} onCancelar={onCancelar} />);
    await userEvent.click(screen.getByRole('button', { name: /Cancelar/i }));
    expect(onCancelar).toHaveBeenCalled();
    // ESC
    onCancelar.mockClear();
    await userEvent.keyboard('{Escape}');
    expect(onCancelar).toHaveBeenCalled();
  });

  it('no contiene fetch directo', () => {
    const content = fs.readFileSync(path.join(__dirname, 'ProveedorBajaDialog.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });
});
