import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ProveedorTabla from './ProveedorTabla.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T04 — ProveedorTabla — RF-1', () => {
  const proveedores = [
    { codigo: 'PROV-001', nombre: 'Central', email: 'a@b.com', telefono: '+34 600', direccion: 'Calle 10' },
    { codigo: 'PROV-002', nombre: 'Norte', email: null, telefono: null, direccion: null },
  ];

  it('renderiza tabla con 5 columnas fijas codigo|nombre|email|telefono|direccion sin estado', () => {
    render(<ProveedorTabla proveedores={proveedores} onEditar={vi.fn()} onBaja={vi.fn()} />);
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByText('Código')).toBeInTheDocument();
    expect(screen.getByText('Nombre')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('Teléfono')).toBeInTheDocument();
    expect(screen.getByText('Dirección')).toBeInTheDocument();
    expect(screen.queryByText('Estado')).not.toBeInTheDocument();
    expect(screen.queryByText(/filtrar/i)).not.toBeInTheDocument();
  });

  it('renderiza 2 filas con 5 celdas con "—" para null y data-testid por fila', () => {
    render(<ProveedorTabla proveedores={proveedores} onEditar={vi.fn()} onBaja={vi.fn()} />);
    const rows = screen.getAllByTestId(/proveedor-fila-/);
    expect(rows).toHaveLength(2);
    expect(screen.getByTestId('proveedor-fila-PROV-001')).toBeInTheDocument();
    expect(screen.getByTestId('proveedor-fila-PROV-002')).toBeInTheDocument();
    expect(screen.getByText('a@b.com')).toBeInTheDocument();
    // 3 "—" para null en segunda fila
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThanOrEqual(3);
    expect(screen.getByText('Central')).toBeInTheDocument();
    expect(screen.getByText('Norte')).toBeInTheDocument();
  });

  it('recibe proveedores y callbacks onEditar/onBaja por props, sin fetch', () => {
    const onEditar = vi.fn();
    const onBaja = vi.fn();
    render(<ProveedorTabla proveedores={proveedores} onEditar={onEditar} onBaja={onBaja} />);
    const content = fs.readFileSync(path.join(__dirname, 'ProveedorTabla.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).not.toMatch(/useProveedores/);
  });

  it('no contiene lógica de paginación, orden o filtros', () => {
    const content = fs.readFileSync(path.join(__dirname, 'ProveedorTabla.jsx'), 'utf8');
    expect(content).not.toMatch(/paginaci/i);
    expect(content).not.toMatch(/orden/i);
    expect(content).not.toMatch(/filtr/i);
  });
});
