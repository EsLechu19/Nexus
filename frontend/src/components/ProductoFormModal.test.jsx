import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ProductoFormModal from './ProductoFormModal.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T05 — ProductoFormModal modo alta — RF-2', () => {
  it('renderiza modal role dialog aria-modal con 4 campos y labels htmlFor', () => {
    render(<ProductoFormModal modo="alta" onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    expect(screen.getByLabelText(/Nombre/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^SKU$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Categoría/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Stock inicial/i)).toBeInTheDocument();
  });

  it('valida solo presencia tras trim sin llamar onSubmit', async () => {
    const onSubmit = vi.fn();
    render(<ProductoFormModal modo="alta" onSubmit={onSubmit} onClose={vi.fn()} />);
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(screen.getByText(/Nombre requerido/i)).toBeInTheDocument();
    expect(screen.getByText(/SKU requerido/i)).toBeInTheDocument();
    expect(screen.getByText(/Categoría requerida/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.queryByText(/Stock requerido/i)).not.toBeInTheDocument(); // stock vacío no bloquea
  });

  it('stock vacío no bloquea y no se envía como 0', async () => {
    const onSubmit = vi.fn();
    render(<ProductoFormModal modo="alta" onSubmit={onSubmit} onClose={vi.fn()} />);
    await userEvent.type(screen.getByLabelText(/Nombre/i), 'Play');
    await userEvent.type(screen.getByLabelText(/^SKU$/i), 'SKU-001');
    await userEvent.selectOptions(screen.getByLabelText(/Categoría/i), 'consola');
    // stock vacío
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ nombre: 'Play', sku: 'SKU-001', categoria: 'consola' }));
    expect(onSubmit.mock.calls[0][0]).not.toHaveProperty('stock_inicial');
  });

  it('prop cargando deshabilita botón Crear', () => {
    render(<ProductoFormModal modo="alta" onSubmit={vi.fn()} onClose={vi.fn()} cargando={true} />);
    expect(screen.getByRole('button', { name: /Crear/i })).toBeDisabled();
  });

  it('no contiene fetch', () => {
    const content = fs.readFileSync(path.join(__dirname, 'ProductoFormModal.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });
});

describe('T06 — ProductoFormModal modo edición — RF-3', () => {
  const producto = { sku: 'PS5-001', nombre: 'Play', categoria: 'consola', stock_inicial: 10 };

  it('precarga nombre/categoria, SKU deshabilitado y stock oculto', () => {
    render(<ProductoFormModal modo="edicion" producto={producto} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByLabelText(/Nombre/i)).toHaveValue('Play');
    expect(screen.getByLabelText(/Categoría/i)).toHaveValue('consola');
    expect(screen.getByLabelText(/^SKU$/i)).toHaveValue('PS5-001');
    expect(screen.getByLabelText(/^SKU$/i)).toBeDisabled();
    expect(screen.queryByLabelText(/Stock inicial/i)).not.toBeInTheDocument();
  });

  it('solo envía nombre/categoria sin sku/stock al submit', async () => {
    const onSubmit = vi.fn();
    render(<ProductoFormModal modo="edicion" producto={producto} onSubmit={onSubmit} onClose={vi.fn()} />);
    await userEvent.clear(screen.getByLabelText(/Nombre/i));
    await userEvent.type(screen.getByLabelText(/Nombre/i), 'Nuevo');
    await userEvent.click(screen.getByRole('button', { name: /Guardar/i }));
    expect(onSubmit).toHaveBeenCalledWith({ nombre: 'Nuevo', categoria: 'consola' });
    expect(onSubmit.mock.calls[0][0]).not.toHaveProperty('sku');
    expect(onSubmit.mock.calls[0][0]).not.toHaveProperty('stock_inicial');
  });

  it('valida solo presencia en edición', async () => {
    const onSubmit = vi.fn();
    render(<ProductoFormModal modo="edicion" producto={producto} onSubmit={onSubmit} onClose={vi.fn()} />);
    await userEvent.clear(screen.getByLabelText(/Nombre/i));
    await userEvent.click(screen.getByRole('button', { name: /Guardar/i }));
    expect(screen.getByText(/Nombre requerido/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});

describe('T15 — Tokens diseño 010 — RF-1/RF-3/RF-4 (botón primario, input error, modal)', () => {
  it('botón primario Crear/Guardar usa bg-primary-500 y focus:ring-primary-500, secundario Cancelar usa bg-white border-neutral-200', () => {
    const { rerender } = render(<ProductoFormModal modo="alta" onSubmit={vi.fn()} onClose={vi.fn()} />);
    const primario = screen.getByRole('button', { name: /Crear/i });
    expect(primario.className).toMatch(/bg-primary-500/);
    expect(primario.className).toMatch(/focus:ring-primary-500/);
    expect(primario.className).toMatch(/disabled:bg-primary-300/);
    const secundario = screen.getByRole('button', { name: /Cancelar/i });
    expect(secundario.className).toMatch(/bg-white/);
    expect(secundario.className).toMatch(/border-neutral-200/);
    expect(secundario.className).toMatch(/focus:ring-primary-500/);
    // edición también primario
    rerender(<ProductoFormModal modo="edicion" producto={{ sku: 'X', nombre: 'N', categoria: 'consola' }} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole('button', { name: /Guardar/i }).className).toMatch(/bg-primary-500/);
  });

  it('input con error usa border-error-600 y label usa text-neutral-700, sin error usa border-neutral-200', async () => {
    render(<ProductoFormModal modo="alta" onSubmit={vi.fn()} onClose={vi.fn()} />);
    const inputNombre = screen.getByLabelText(/Nombre/i);
    expect(inputNombre.className).toMatch(/border-neutral-200/);
    expect(inputNombre.className).toMatch(/focus:ring-primary-500/);
    const label = document.querySelector('label[for="producto-nombre"]');
    expect(label.className).toMatch(/text-neutral-700/);
    expect(label.className).toMatch(/text-sm/);
    // disparar validación
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(await screen.findByText(/Nombre requerido/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Nombre/i).className).toMatch(/border-error-600/);
  });

  it('modal usa overlay bg-neutral-900/50 y contenedor bg-neutral-0 rounded-lg p-6 gap-4', () => {
    const { container } = render(<ProductoFormModal modo="alta" onSubmit={vi.fn()} onClose={vi.fn()} />);
    const dialog = screen.getByRole('dialog');
    expect(dialog.className).toMatch(/bg-neutral-0/);
    expect(dialog.className).toMatch(/rounded-lg/);
    expect(dialog.className).toMatch(/p-6/);
    expect(dialog.className).toMatch(/gap-4/);
    // overlay es padre del dialog
    expect(dialog.parentElement.className).toMatch(/bg-neutral-900\/50/);
    expect(dialog.parentElement.className).toMatch(/fixed inset-0/);
    // fuente no hardcodeada
    const content = fs.readFileSync(path.join(__dirname, 'ProductoFormModal.jsx'), 'utf8');
    expect(content).not.toMatch(/#[0-9a-fA-F]{3,6}/);
    expect(content).toMatch(/bg-neutral-0/);
  });
});
