import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ProductoTabla from './ProductoTabla.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T04 — ProductoTabla — RF-1', () => {
  const productos = [
    { sku: 'PS5-001', nombre: 'PlayStation 5', categoria: 'consola', stock_inicial: 10 },
    { sku: 'ZELDA-001', nombre: 'Zelda', categoria: 'videojuego', stock_inicial: 0 },
  ];

  it('renderiza tabla con 4 columnas fijas sin filtros/paginación', () => {
    render(<ProductoTabla productos={productos} onEditar={vi.fn()} onBaja={vi.fn()} />);
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByText('SKU')).toBeInTheDocument();
    expect(screen.getByText('Nombre')).toBeInTheDocument();
    expect(screen.getByText('Categoría')).toBeInTheDocument();
    expect(screen.getByText('Stock inicial')).toBeInTheDocument();
    // no columna estado
    expect(screen.queryByText('Estado')).not.toBeInTheDocument();
    expect(screen.queryByText(/filtrar/i)).not.toBeInTheDocument();
  });

  it('renderiza 2 filas con 4 celdas y data-testid por fila', () => {
    render(<ProductoTabla productos={productos} onEditar={vi.fn()} onBaja={vi.fn()} />);
    const rows = screen.getAllByTestId(/producto-fila-/);
    expect(rows).toHaveLength(2);
    expect(screen.getByTestId('producto-fila-PS5-001')).toBeInTheDocument();
    expect(screen.getByText('PlayStation 5')).toBeInTheDocument();
    expect(screen.getByText('consola')).toBeInTheDocument();
  });

  it('recibe productos y callbacks onEditar/onBaja por props, sin fetch', () => {
    const onEditar = vi.fn();
    const onBaja = vi.fn();
    render(<ProductoTabla productos={productos} onEditar={onEditar} onBaja={onBaja} />);
    const content = fs.readFileSync(path.join(__dirname, 'ProductoTabla.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).not.toMatch(/useProductos/);
  });

  it('no contiene lógica de paginación u ordenamiento', () => {
    const content = fs.readFileSync(path.join(__dirname, 'ProductoTabla.jsx'), 'utf8');
    expect(content).not.toMatch(/paginaci/i);
    expect(content).not.toMatch(/orden/i);
  });
});
