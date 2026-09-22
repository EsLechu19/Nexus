import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ProveedorFormModal from './ProveedorFormModal.jsx';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('T05 — ProveedorFormModal modo alta — RF-2', () => {
  it('renderiza modal role dialog aria-modal con 5 campos y labels htmlFor', () => {
    render(<ProveedorFormModal modo="alta" onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    expect(screen.getByLabelText(/Código/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Nombre/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Teléfono/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Dirección/i)).toBeInTheDocument();
    // htmlFor asociado
    const codigoInput = screen.getByLabelText(/Código/i);
    expect(codigoInput).toHaveAttribute('id', 'proveedor-codigo');
    const nombreInput = screen.getByLabelText(/Nombre/i);
    expect(nombreInput).toHaveAttribute('id', 'proveedor-nombre');
  });

  it('valida solo presencia tras trim sin llamar onSubmit', async () => {
    const onSubmit = vi.fn();
    render(<ProveedorFormModal modo="alta" onSubmit={onSubmit} onClose={vi.fn()} />);
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(screen.getByText(/Código requerido/i)).toBeInTheDocument();
    expect(screen.getByText(/Nombre requerido/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('opcional con espacios "   " muestra "No puede quedar vacío" sin fetch', async () => {
    const onSubmit = vi.fn();
    render(<ProveedorFormModal modo="alta" onSubmit={onSubmit} onClose={vi.fn()} />);
    await userEvent.type(screen.getByLabelText(/Código/i), 'PROV-001');
    await userEvent.type(screen.getByLabelText(/Nombre/i), 'Central');
    await userEvent.type(screen.getByLabelText(/Email/i), '   ');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(screen.getByText(/No puede quedar vacío/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
    // telefono con espacios también bloquea
    await userEvent.clear(screen.getByLabelText(/Email/i));
    await userEvent.type(screen.getByLabelText(/Teléfono/i), '   ');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(screen.getAllByText(/No puede quedar vacío/i).length).toBeGreaterThanOrEqual(1);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('envía payload con opcionales omitidos si vacíos y sin llamar fetch', async () => {
    const onSubmit = vi.fn();
    render(<ProveedorFormModal modo="alta" onSubmit={onSubmit} onClose={vi.fn()} />);
    await userEvent.type(screen.getByLabelText(/Código/i), 'PROV-001');
    await userEvent.type(screen.getByLabelText(/Nombre/i), 'Central');
    // opcionales vacíos
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ codigo: 'PROV-001', nombre: 'Central' }));
    expect(onSubmit.mock.calls[0][0]).not.toHaveProperty('email');
    expect(onSubmit.mock.calls[0][0]).not.toHaveProperty('telefono');
    expect(onSubmit.mock.calls[0][0]).not.toHaveProperty('direccion');
    // con opcionales informados se envían trim
    onSubmit.mockClear();
    await userEvent.type(screen.getByLabelText(/Email/i), 'a@b.com');
    await userEvent.type(screen.getByLabelText(/Teléfono/i), '+34 600');
    await userEvent.type(screen.getByLabelText(/Dirección/i), 'Calle 10');
    await userEvent.click(screen.getByRole('button', { name: /Crear/i }));
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ codigo: 'PROV-001', nombre: 'Central', email: 'a@b.com', telefono: '+34 600', direccion: 'Calle 10' }));
  });

  it('prop cargando deshabilita botón Crear', () => {
    render(<ProveedorFormModal modo="alta" onSubmit={vi.fn()} onClose={vi.fn()} cargando={true} />);
    expect(screen.getByRole('button', { name: /Crear/i })).toBeDisabled();
  });

  it('no contiene fetch', () => {
    const content = fs.readFileSync(path.join(__dirname, 'ProveedorFormModal.jsx'), 'utf8');
    expect(content).not.toMatch(/fetch\s*\(/);
  });
});

describe('T06 — ProveedorFormModal modo edición — RF-3', () => {
  const proveedor = { codigo: 'PROV-001', nombre: 'Central', email: null, telefono: '+34 600', direccion: null };

  it('precarga nombre/email/telefono/direccion (null→"" vacío) y codigo visible disabled', () => {
    render(<ProveedorFormModal modo="edicion" proveedor={proveedor} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByLabelText(/Nombre/i)).toHaveValue('Central');
    expect(screen.getByLabelText(/Email/i)).toHaveValue('');
    expect(screen.getByLabelText(/Teléfono/i)).toHaveValue('+34 600');
    expect(screen.getByLabelText(/Dirección/i)).toHaveValue('');
    const codigoInput = screen.getByLabelText(/Código/i);
    expect(codigoInput).toHaveValue('PROV-001');
    expect(codigoInput).toBeDisabled();
  });

  it('codigo excluido del payload y botón Borrar por campo opcional envía null explícito', async () => {
    const onSubmit = vi.fn();
    render(<ProveedorFormModal modo="edicion" proveedor={proveedor} onSubmit={onSubmit} onClose={vi.fn()} />);
    // Borrar email (que ya es null→"" pero marcamos null explícito)
    const borrarBotones = screen.getAllByRole('button', { name: /Borrar/i });
    expect(borrarBotones.length).toBeGreaterThanOrEqual(3);
    // clicar Borrar email (primer borrador corresponde a email)
    await userEvent.click(borrarBotones[0]);
    // cambiar nombre para tener algo que enviar
    await userEvent.clear(screen.getByLabelText(/Nombre/i));
    await userEvent.type(screen.getByLabelText(/Nombre/i), 'Nuevo');
    await userEvent.click(screen.getByRole('button', { name: /Guardar/i }));
    expect(onSubmit).toHaveBeenCalled();
    const payload = onSubmit.mock.calls[0][0];
    expect(payload).not.toHaveProperty('codigo');
    expect(payload).toHaveProperty('email', null);
    expect(payload).not.toHaveProperty('estado');
  });

  it('campo no tocado se omite, ""/ "   " bloquea local sin fetch', async () => {
    const onSubmit = vi.fn();
    render(<ProveedorFormModal modo="edicion" proveedor={proveedor} onSubmit={onSubmit} onClose={vi.fn()} />);
    // sin tocar opcionales, solo cambiar nombre
    await userEvent.clear(screen.getByLabelText(/Nombre/i));
    await userEvent.type(screen.getByLabelText(/Nombre/i), 'Central 2');
    await userEvent.click(screen.getByRole('button', { name: /Guardar/i }));
    let payload = onSubmit.mock.calls[0][0];
    expect(payload).toEqual({ nombre: 'Central 2' });
    expect(payload).not.toHaveProperty('email');
    expect(payload).not.toHaveProperty('telefono');
    expect(payload).not.toHaveProperty('direccion');

    // ahora poner email a "   " debe bloquear
    onSubmit.mockClear();
    await userEvent.type(screen.getByLabelText(/Email/i), '   ');
    await userEvent.click(screen.getByRole('button', { name: /Guardar/i }));
    expect(screen.getByText(/No puede quedar vacío/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();

    // vacío "" también bloquea si fue tocado
    await userEvent.clear(screen.getByLabelText(/Email/i));
    // dejar vacío tras tocar -> debe bloquear? según spec "" tras trim bloquea
    // simulamos escribir y borrar
    await userEvent.type(screen.getByLabelText(/Email/i), 'a');
    await userEvent.clear(screen.getByLabelText(/Email/i));
    await userEvent.click(screen.getByRole('button', { name: /Guardar/i }));
    expect(screen.getByText(/No puede quedar vacío/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('null vs "" vs ausente: null envía null, "" bloquea, ausente omite', async () => {
    const onSubmit = vi.fn();
    const prov2 = { codigo: 'PROV-002', nombre: 'Norte', email: 'a@b.com', telefono: null, direccion: 'Calle 1' };
    render(<ProveedorFormModal modo="edicion" proveedor={prov2} onSubmit={onSubmit} onClose={vi.fn()} />);
    // Borrar telefono (null) -> debe enviar null
    const borrarTel = screen.getAllByRole('button', { name: /Borrar/i })[1];
    await userEvent.click(borrarTel);
    await userEvent.click(screen.getByRole('button', { name: /Guardar/i }));
    // si solo borramos telefono y no tocamos nombre, payload debe tener solo telefono null? pero nombre no cambiado se omite, entonces payload {telefono: null}
    // según spec si nombre sin cambios y contacto borrado, se envía solo null
    let payload = onSubmit.mock.calls[0][0];
    expect(payload).toEqual({ telefono: null });
  });
});
