import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import MovimientosHistorial from './MovimientosHistorial.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T04 — MovimientosHistorial — RF-1', () => {
  const movimientos = [
    { id: 16, producto_codigo: 'PROD-003', proveedor_codigo: null, tipo: 'salida', cantidad: 8, motivo: 'Venta mostrador', fecha: '2026-09-08T12:00:00Z' },
    { id: 15, producto_codigo: 'PROD-003', proveedor_codigo: 'PROV-002', tipo: 'entrada', cantidad: 10, motivo: null, fecha: '2026-09-08T11:00:00Z' },
  ];

  it('renderiza tabla con 7 columnas fijas fecha|producto|proveedor|tipo|cantidad|motivo|id sin filtros/paginación', () => {
    render(<MovimientosHistorial movimientos={movimientos} />);
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByText('Fecha')).toBeInTheDocument();
    expect(screen.getByText('Producto')).toBeInTheDocument();
    expect(screen.getByText('Proveedor')).toBeInTheDocument();
    expect(screen.getByText('Tipo')).toBeInTheDocument();
    expect(screen.getByText('Cantidad')).toBeInTheDocument();
    expect(screen.getByText('Motivo')).toBeInTheDocument();
    // id column header (exact "ID" or "id")
    expect(screen.getByText(/^id$/i)).toBeInTheDocument();
    expect(screen.queryByText(/filtrar/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/pagin/i)).not.toBeInTheDocument();
  });

  it('renderiza 2 filas con 7 celdas con "—" para proveedor/motivo null y data-testid por fila', () => {
    render(<MovimientosHistorial movimientos={movimientos} />);
    const rows = screen.getAllByTestId(/movimiento-fila-/);
    expect(rows).toHaveLength(2);
    expect(screen.getByTestId('movimiento-fila-16')).toBeInTheDocument();
    expect(screen.getByTestId('movimiento-fila-15')).toBeInTheDocument();
    // primera fila tiene proveedor null -> "—" y motivo "Venta mostrador"
    // segunda fila tiene motivo null -> "—"
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('PROD-003')).toHaveLength(2);
    expect(screen.getByText('salida')).toBeInTheDocument();
    expect(screen.getByText('entrada')).toBeInTheDocument();
    // fecha ISO sin formateo
    expect(screen.getByText('2026-09-08T12:00:00Z')).toBeInTheDocument();
    expect(screen.getByText('2026-09-08T11:00:00Z')).toBeInTheDocument();
    // motivo largo sin truncar (verificar que se muestra completo)
    expect(screen.getByText('Venta mostrador')).toBeInTheDocument();
  });

  it('recibe movimientos por props, sin fetch, sin ordenar', () => {
    const content = fs.readFileSync(path.join(__dirname, 'MovimientosHistorial.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).not.toMatch(/useMovimientos/);
    expect(content).not.toMatch(/sort\(/i);
    // verificar que usa movimientos prop directamente
    expect(content).toMatch(/movimientos/);
  });

  it('no contiene lógica de paginación u ordenamiento y sin columna stock', () => {
    const content = fs.readFileSync(path.join(__dirname, 'MovimientosHistorial.jsx'), 'utf8');
    expect(content).not.toMatch(/paginaci/i);
    expect(content).not.toMatch(/orden/i);
    expect(content).not.toMatch(/stock_actual/i);
    expect(content).not.toMatch(/filtr/i);
  });
});
