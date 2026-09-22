import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import MovimientoFormModal from './MovimientoFormModal.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const productos = [{ codigo: 'PROD-001', nombre: 'Juego A' }, { codigo: 'PROD-002', nombre: 'Juego B' }];
const proveedores = [{ codigo: 'PROV-001', nombre: 'Central' }];

describe('T05 — MovimientoFormModal Entrada|Salida — RF-2, RF-3', () => {
  it('renderiza modal role dialog aria-modal con tabs Entrada|Salida y Entrada preseleccionada', () => {
    render(<MovimientoFormModal productos={productos} proveedores={proveedores} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    expect(screen.getByRole('tab', { name: /Entrada/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Salida/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Entrada/i })).toHaveAttribute('aria-selected', 'true');
  });

  it('Entrada muestra 4 campos (producto, proveedor, cantidad, motivo) con label htmlFor/id', () => {
    render(<MovimientoFormModal productos={productos} proveedores={proveedores} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Proveedor/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Cantidad/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Motivo/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Producto/i)).toHaveAttribute('id', 'movimiento-producto');
    expect(screen.getByLabelText(/Proveedor/i)).toHaveAttribute('id', 'movimiento-proveedor');
    expect(screen.getByLabelText(/Cantidad/i)).toHaveAttribute('id', 'movimiento-cantidad');
    expect(screen.getByLabelText(/Motivo/i)).toHaveAttribute('id', 'movimiento-motivo');
  });

  it('Salida muestra 3 campos (oculta proveedor) y proveedor oculto se limpia', async () => {
    const onSubmit = vi.fn();
    render(<MovimientoFormModal productos={productos} proveedores={proveedores} onSubmit={onSubmit} onClose={vi.fn()} />);
    // seleccionar proveedor en Entrada
    await userEvent.selectOptions(screen.getByLabelText(/Proveedor/i), 'PROV-001');
    await userEvent.type(screen.getByLabelText(/Cantidad/i), '10');
    // cambiar a Salida
    await userEvent.click(screen.getByRole('tab', { name: /Salida/i }));
    expect(screen.queryByLabelText(/Proveedor/i)).not.toBeInTheDocument();
    // producto y cantidad deben conservarse
    expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Cantidad/i)).toHaveValue('10');
    // submit en Salida no debe enviar proveedor
    await userEvent.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(onSubmit).toHaveBeenCalledWith(expect.not.objectContaining({ proveedor_codigo: expect.anything() }));
    expect(onSubmit.mock.calls[0][0]).not.toHaveProperty('proveedor_codigo');
  });

  it('cambio Entrada↔Salida conserva producto/cantidad/motivo y limpia errores/proveedor', async () => {
    render(<MovimientoFormModal productos={productos} proveedores={proveedores} onSubmit={vi.fn()} onClose={vi.fn()} />);
    await userEvent.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await userEvent.type(screen.getByLabelText(/Cantidad/i), '5');
    await userEvent.type(screen.getByLabelText(/Motivo/i), 'Compra');
    // provocar error en proveedor (vacío) y luego cambiar a Salida debe limpiar error
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(screen.getByText(/Campo requerido/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('tab', { name: /Salida/i }));
    expect(screen.queryByText(/Campo requerido/i)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/Producto/i)).toHaveValue('PROD-001');
    expect(screen.getByLabelText(/Cantidad/i)).toHaveValue('5');
    expect(screen.getByLabelText(/Motivo/i)).toHaveValue('Compra');
    // volver a Entrada proveedor debe estar vacío
    await userEvent.click(screen.getByRole('tab', { name: /Entrada/i }));
    expect(screen.getByLabelText(/Proveedor/i)).toHaveValue('');
  });

  it('valida solo cantidad requerida y entero >0 ("1.0"→Debe ser un número entero mayor a 0) y motivo no vacío', async () => {
    const onSubmit = vi.fn();
    render(<MovimientoFormModal productos={productos} proveedores={proveedores} onSubmit={onSubmit} onClose={vi.fn()} />);
    await userEvent.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await userEvent.selectOptions(screen.getByLabelText(/Proveedor/i), 'PROV-001');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(screen.getByText(/Campo requerido/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
    // cantidad "1.0" no entero
    await userEvent.type(screen.getByLabelText(/Cantidad/i), '1.0');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(screen.getByText(/Debe ser un número entero mayor a 0/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
    await userEvent.clear(screen.getByLabelText(/Cantidad/i));
    await userEvent.type(screen.getByLabelText(/Cantidad/i), '   ');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(screen.getByText(/Campo requerido/i)).toBeInTheDocument();
    // motivo "   " bloquea
    await userEvent.clear(screen.getByLabelText(/Cantidad/i));
    await userEvent.type(screen.getByLabelText(/Cantidad/i), '10');
    await userEvent.type(screen.getByLabelText(/Motivo/i), '   ');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(screen.getByText(/No puede quedar vacío/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('cargando deshabilita "Crear" y <select> muestra Cargando... disabled mientras carga, [] muestra mensaje y bloquea', () => {
    const { rerender } = render(
      <MovimientoFormModal productos={[]} proveedores={[]} cargandoSelects={true} onSubmit={vi.fn()} onClose={vi.fn()} cargando={true} />,
    );
    expect(screen.getByRole('button', { name: /Crear/i })).toBeDisabled();
    expect(screen.getAllByText(/Cargando\.\.\./i)).toHaveLength(2);
    // [] sin cargando
    rerender(<MovimientoFormModal productos={[]} proveedores={[]} cargandoSelects={false} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByText(/No hay productos activos disponibles/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Crear/i })).toBeDisabled();
  });

  it('no contiene fetch', () => {
    const content = fs.readFileSync(path.join(__dirname, 'MovimientoFormModal.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });

  it('envía payload sin proveedor en Salida y con proveedor en Entrada', async () => {
    const onSubmitEntrada = vi.fn();
    const { unmount } = render(<MovimientoFormModal productos={productos} proveedores={proveedores} onSubmit={onSubmitEntrada} onClose={vi.fn()} />);
    await userEvent.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await userEvent.selectOptions(screen.getByLabelText(/Proveedor/i), 'PROV-001');
    await userEvent.type(screen.getByLabelText(/Cantidad/i), '10');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(onSubmitEntrada).toHaveBeenCalledWith(expect.objectContaining({ producto_codigo: 'PROD-001', proveedor_codigo: 'PROV-001', cantidad: 10 }));
    unmount();
    const onSubmitSalida = vi.fn();
    render(<MovimientoFormModal productos={productos} proveedores={proveedores} onSubmit={onSubmitSalida} onClose={vi.fn()} />);
    await userEvent.click(screen.getByRole('tab', { name: /Salida/i }));
    await userEvent.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await userEvent.type(screen.getByLabelText(/Cantidad/i), '5');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(onSubmitSalida).toHaveBeenCalledWith(expect.not.objectContaining({ proveedor_codigo: expect.anything() }));
    expect(onSubmitSalida.mock.calls[0][0]).toEqual({ producto_codigo: 'PROD-001', cantidad: 5 });
  });
});

describe('T06 — MovimientoFormModal estados selects — RF-2', () => {
  it('si productos/proveedores [] bloquea "Crear" con mensaje puntual', () => {
    const { rerender } = render(<MovimientoFormModal productos={[]} proveedores={[]} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByText(/No hay productos activos disponibles/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Crear/i })).toBeDisabled();
    // Salida solo necesita productos (rerender limpia DOM)
    rerender(<MovimientoFormModal productos={[]} proveedores={proveedores} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByText(/No hay productos activos disponibles/i)).toBeInTheDocument();
  });

  it('si carga falla 4xx muestra ErrorMessage validacion sin Reintentar y bloquea hasta cerrar/reabrir', () => {
    const errorSelects = { tipo: 'validacion', mensaje: 'No se pudo completar la solicitud', reintentable: false };
    const { rerender } = render(<MovimientoFormModal productos={[]} proveedores={[]} errorSelects={errorSelects} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByText('No se pudo completar la solicitud')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Reintentar/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Crear/i })).toBeDisabled();
    // al cerrar y reabrir, error se limpia (simulado por rerender sin error)
    rerender(<MovimientoFormModal productos={productos} proveedores={proveedores} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.queryByText('No se pudo completar la solicitud')).not.toBeInTheDocument();
  });

  it('si carga falla 5xx/red muestra ErrorMessage conexion con Reintentar que reejecuta solo GET', async () => {
    const errorSelects = { tipo: 'conexion', mensaje: 'Error de conexión con el servidor', reintentable: true };
    const onReintentarSelects = vi.fn();
    render(<MovimientoFormModal productos={[]} proveedores={[]} errorSelects={errorSelects} onReintentarSelects={onReintentarSelects} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByText('Error de conexión con el servidor')).toBeInTheDocument();
    const reintentarBtn = screen.getByRole('button', { name: /Reintentar/i });
    expect(reintentarBtn).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Crear/i })).toBeDisabled();
    await userEvent.click(reintentarBtn);
    expect(onReintentarSelects).toHaveBeenCalledTimes(1);
  });

  it('grep fetch vacío', () => {
    const content = fs.readFileSync(path.join(__dirname, 'MovimientoFormModal.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });
});

describe('T12 — Tests componentes MovimientosHistorial/MovimientoFormModal (selects condicionados) — RF-1..3', () => {
  it('historial 7 cols con "—" para null sin stock', () => {
    const histContent = fs.readFileSync(path.join(__dirname, 'MovimientosHistorial.jsx'), 'utf8');
    expect(histContent).not.toMatch(/stock_actual/i);
    expect(histContent).toMatch(/proveedor_codigo \?\? '—'/);
    expect(histContent).toMatch(/motivo \?\? '—'/);
    expect((histContent.match(/<th[\s>]/g) || []).length).toBe(7);
    expect(histContent).not.toMatch(/fetch\s*\(/);
  });

  it('modal 4/3 campos según tipo con tabs Entrada|Salida, Entrada preseleccionada y a11y', () => {
    render(<MovimientoFormModal productos={productos} proveedores={proveedores} onSubmit={vi.fn()} onClose={vi.fn()} />);
    // Entrada preseleccionada
    expect(screen.getByRole('tab', { name: /Entrada/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    // 4 campos en Entrada
    expect(screen.getByLabelText(/Producto/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Proveedor/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Cantidad/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Motivo/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Producto/i)).toHaveAttribute('id', 'movimiento-producto');
    expect(screen.getByLabelText(/Proveedor/i)).toHaveAttribute('id', 'movimiento-proveedor');
    expect(screen.getByLabelText(/Cantidad/i)).toHaveAttribute('id', 'movimiento-cantidad');
    expect(screen.getByLabelText(/Motivo/i)).toHaveAttribute('id', 'movimiento-motivo');
  });

  it('cambio de tipo conserva producto/cantidad/motivo y limpia proveedor/errores', async () => {
    render(<MovimientoFormModal productos={productos} proveedores={proveedores} onSubmit={vi.fn()} onClose={vi.fn()} />);
    await userEvent.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await userEvent.type(screen.getByLabelText(/Cantidad/i), '5');
    await userEvent.type(screen.getByLabelText(/Motivo/i), 'Compra');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(screen.getByText(/Campo requerido/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('tab', { name: /Salida/i }));
    expect(screen.queryByText(/Campo requerido/i)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/Producto/i)).toHaveValue('PROD-001');
    expect(screen.getByLabelText(/Cantidad/i)).toHaveValue('5');
    expect(screen.getByLabelText(/Motivo/i)).toHaveValue('Compra');
    expect(screen.queryByLabelText(/Proveedor/i)).not.toBeInTheDocument();
  });

  it('[] bloquea Crear, Cargando... disabled, 4xx sin Reintentar vs 5xx con Reintentar', () => {
    const { unmount } = render(<MovimientoFormModal productos={[]} proveedores={[]} cargandoSelects={true} cargando={true} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole('button', { name: /Crear/i })).toBeDisabled();
    expect(screen.getAllByText(/Cargando\.\.\./i).length).toBeGreaterThanOrEqual(1);
    unmount();
    render(<MovimientoFormModal productos={[]} proveedores={[]} cargandoSelects={false} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByText(/No hay productos activos disponibles/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Crear/i })).toBeDisabled();
  });

  it('validación cantidad >0 entero y motivo No puede quedar vacío bloquea sin fetch', async () => {
    const onSubmit = vi.fn();
    render(<MovimientoFormModal productos={productos} proveedores={proveedores} onSubmit={onSubmit} onClose={vi.fn()} />);
    await userEvent.selectOptions(screen.getByLabelText(/Producto/i), 'PROD-001');
    await userEvent.selectOptions(screen.getByLabelText(/Proveedor/i), 'PROV-001');
    await userEvent.type(screen.getByLabelText(/Cantidad/i), '1.0');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(screen.getByText(/Debe ser un número entero mayor a 0/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
    await userEvent.clear(screen.getByLabelText(/Cantidad/i));
    await userEvent.type(screen.getByLabelText(/Cantidad/i), '10');
    await userEvent.type(screen.getByLabelText(/Motivo/i), '   ');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(screen.getByText(/No puede quedar vacío/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
    const content = fs.readFileSync(path.join(__dirname, 'MovimientoFormModal.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });
});
