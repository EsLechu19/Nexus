import React from 'react';

/**
 * Tabla presentacional de proveedores — RF-1
 * 5 columnas fijas codigo|nombre|email|telefono|direccion, "—" para null, sin fetch.
 */
export default function ProveedorTabla({ proveedores = [], onEditar, onBaja }) {
  return (
    <table className="w-full divide-y divide-neutral-200">
      <thead>
        <tr>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Código</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Nombre</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Email</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Teléfono</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Dirección</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Acciones</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-neutral-200">
        {proveedores.map((p) => (
          <tr key={p.codigo} data-testid={`proveedor-fila-${p.codigo}`} className="hover:bg-neutral-50">
            <td className="p-3 text-sm border-t border-neutral-200">{p.codigo}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{p.nombre}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{p.email ?? '—'}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{p.telefono ?? '—'}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{p.direccion ?? '—'}</td>
            <td className="p-3 text-sm border-t border-neutral-200">
              <button type="button" onClick={() => onEditar?.(p)} className="bg-white text-neutral-700 border border-neutral-200 hover:bg-neutral-50 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-neutral-100 disabled:cursor-not-allowed">
                Editar
              </button>
              <button type="button" onClick={() => onBaja?.(p)} className="bg-error-600 text-white hover:bg-error-700 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-error-300 disabled:cursor-not-allowed">
                Dar de baja
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
