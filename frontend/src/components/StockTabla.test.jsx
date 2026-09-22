import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import StockTabla from './StockTabla.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T03 — StockTabla — RF-1', () => {
  const stock = [
    { codigo: 'PROD-001', nombre: 'PlayStation 5 Slim', stock_actual: 14, stock_minimo: 10, alerta: false },
    { codigo: 'PROD-002', nombre: 'Zelda TOTK con nombre muy largo para probar salto de línea sin truncar', stock_actual: 0, stock_minimo: 5, alerta: true },
  ];

  it('renderiza tabla con 5 columnas fijas codigo|nombre|stock_actual|stock_minimo|alerta sin filtros/paginación/acciones', () => {
    render(<StockTabla stock={stock} />);
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByText('Codigo')).toBeInTheDocument();
    expect(screen.getByText('Nombre')).toBeInTheDocument();
    expect(screen.getByText('Stock actual')).toBeInTheDocument();
    expect(screen.getByText('Stock minimo')).toBeInTheDocument();
    expect(screen.getByText('Alerta')).toBeInTheDocument();
    expect(screen.queryByText(/filtrar/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/pagin/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/estado/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('renderiza 2 filas con 5 celdas, badge Bajo stock + fila marcada si alerta true y — si false, stock_minimo 0→0, data-testid', () => {
    render(<StockTabla stock={stock} />);
    const filas = screen.getAllByTestId(/stock-fila-/);
    expect(filas).toHaveLength(2);
    expect(screen.getByTestId('stock-fila-PROD-001')).toBeInTheDocument();
    expect(screen.getByTestId('stock-fila-PROD-002')).toBeInTheDocument();
    // PROD-001 alerta false → — sin marca
    expect(screen.getByTestId('stock-fila-PROD-001').textContent).toContain('—');
    // PROD-002 alerta true → badge Bajo stock + fila marcada
    expect(screen.getByText('Bajo stock')).toBeInTheDocument();
    const filaAlerta = screen.getByTestId('stock-fila-PROD-002');
    // fila marcada: clase o atributo visual (ej. bg-alerta-50 o data-alerta)
    expect(filaAlerta.className + filaAlerta.getAttribute('data-alerta') || '').toMatch(/alerta|Bajo/i);
    // stock_minimo 5 y 10 se muestran como "5" y "10", no "—"
    expect(screen.getByTestId('stock-fila-PROD-002').textContent).toContain('5');
    // nombre largo sin truncar
    expect(screen.getByText(/Zelda TOTK con nombre muy largo/)).toBeInTheDocument();
  });

  it('recibe stock ya filtrado por props, sin fetch, sin reordenar', () => {
    const content = fs.readFileSync(path.join(__dirname, 'StockTabla.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
    expect(content).not.toMatch(/useStock/);
    expect(content).not.toMatch(/sort\(/i);
    expect(content).toMatch(/stock/);
  });

  it('no contiene lógica de paginación, filtros ni acciones', () => {
    const content = fs.readFileSync(path.join(__dirname, 'StockTabla.jsx'), 'utf8');
    expect(content).not.toMatch(/pagin/i);
    // filtr en lógica (no en comentario "depurado") — verificar que no hay sort ni fetch para filtrar
    expect(content).not.toMatch(/onEditar|onBaja|onCrear/i);
    expect(content).not.toMatch(/localStorage/);
  });
});

describe('T04 — Manejar null y filas corruptas — RF-1', () => {
  it('stock_minimo 0 muestra "0" no "—", alerta true badge+fila marcada nunca solo color, alerta false "—" sin marca', () => {
    const stock = [
      { codigo: 'PROD-001', nombre: 'A', stock_actual: 5, stock_minimo: 0, alerta: false },
      { codigo: 'PROD-002', nombre: 'B', stock_actual: 0, stock_minimo: 5, alerta: true },
    ];
    render(<StockTabla stock={stock} />);
    const fila0 = screen.getByTestId('stock-fila-PROD-001');
    expect(fila0.textContent).toContain('0');
    expect(fila0.textContent).not.toMatch(/^—$/m);
    expect(fila0.getAttribute('data-alerta')).toBe('false');
    expect(fila0.className).not.toMatch(/red/);
    expect(fila0.textContent).toContain('—');
    const filaAlerta = screen.getByTestId('stock-fila-PROD-002');
    expect(screen.getByText('Bajo stock')).toBeInTheDocument();
    expect(filaAlerta.getAttribute('data-alerta')).toBe('true');
    expect(filaAlerta.className).toMatch(/alerta|bg-alerta/);
    expect(filaAlerta.textContent).toContain('Bajo stock');
  });

  it('fila con codigo number/alerta string/stock_actual float/null se omite sin inventar 0/—', () => {
    const stock = [
      { codigo: 'PROD-001', nombre: 'Valida', stock_actual: 5, stock_minimo: 10, alerta: true },
      { codigo: 123, nombre: 'Codigo number', stock_actual: 5, stock_minimo: 10, alerta: true },
      { codigo: 'PROD-003', nombre: 'Alerta string', stock_actual: 5, stock_minimo: 10, alerta: 'true' },
      { codigo: 'PROD-004', nombre: 'Float', stock_actual: 5.5, stock_minimo: 10, alerta: true },
      { codigo: 'PROD-005', nombre: null, stock_actual: 5, stock_minimo: 10, alerta: true },
      { codigo: 'PROD-006', nombre: 'Extra', stock_actual: 5, stock_minimo: 0, alerta: false, stock_inicial: 99, entradas: 10, salidas: 5 },
    ];
    render(<StockTabla stock={stock} />);
    // solo 2 válidas deben renderizar: PROD-001 y PROD-006 (PROD-006 es válida a pesar de extra fields)
    expect(screen.getByTestId('stock-fila-PROD-001')).toBeInTheDocument();
    expect(screen.getByTestId('stock-fila-PROD-006')).toBeInTheDocument();
    expect(screen.queryByTestId('stock-fila-123')).not.toBeInTheDocument();
    expect(screen.queryByTestId('stock-fila-PROD-003')).not.toBeInTheDocument();
    expect(screen.queryByTestId('stock-fila-PROD-004')).not.toBeInTheDocument();
    expect(screen.queryByTestId('stock-fila-PROD-005')).not.toBeInTheDocument();
    // extra fields ignorados: no deben aparecer 99, 10, 5
    expect(screen.queryByText('99')).not.toBeInTheDocument();
    expect(screen.getAllByTestId(/stock-fila-/)).toHaveLength(2);
  });

  it('grep fetch vacío en StockTabla', () => {
    const content = fs.readFileSync(path.join(__dirname, 'StockTabla.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });
});

describe('T14 — Tokens diseño 010 — RF-1/RF-2/RF-5 (badge migración bg-red-50→bg-alerta-50)', () => {
  it('badge alerta true usa bg-alerta-50 en fila y bg-alerta-100 en badge, nunca bg-red-50', () => {
    const stock = [
      { codigo: 'PROD-001', nombre: 'A', stock_actual: 0, stock_minimo: 5, alerta: true },
      { codigo: 'PROD-002', nombre: 'B', stock_actual: 10, stock_minimo: 5, alerta: false },
    ];
    render(<StockTabla stock={stock} />);
    const filaAlerta = screen.getByTestId('stock-fila-PROD-001');
    expect(filaAlerta.className).toMatch(/bg-alerta-50/);
    expect(filaAlerta.className).not.toMatch(/bg-red-50/);
    const badge = screen.getByText('Bajo stock');
    expect(badge.className).toMatch(/bg-alerta-100/);
    expect(badge.className).toMatch(/text-alerta-600/);
    // fuente no hardcodeada
    const content = fs.readFileSync(path.join(__dirname, 'StockTabla.jsx'), 'utf8');
    expect(content).not.toMatch(/bg-red-50/);
    expect(content).toMatch(/bg-alerta-50/);
    // alerta false muestra — sin bg-alerta
    const filaNoAlerta = screen.getByTestId('stock-fila-PROD-002');
    expect(filaNoAlerta.textContent).toContain('—');
    expect(filaNoAlerta.className).not.toMatch(/bg-alerta-50/);
  });

  it('th usa bg-neutral-100 y td p-3 border-neutral-200', () => {
    const stock = [{ codigo: 'PROD-001', nombre: 'A', stock_actual: 5, stock_minimo: 10, alerta: false }];
    const { container } = render(<StockTabla stock={stock} />);
    const ths = container.querySelectorAll('th');
    expect(ths.length).toBe(5);
    ths.forEach((th) => {
      expect(th.className).toMatch(/bg-neutral-100/);
      expect(th.className).toMatch(/p-3/);
    });
    const tds = container.querySelectorAll('td');
    expect(tds[0].className).toMatch(/p-3/);
    expect(tds[0].className).toMatch(/border-neutral-200/);
  });
});
