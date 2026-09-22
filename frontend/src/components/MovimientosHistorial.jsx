import React from 'react';

/**
 * Tabla presentacional de historial de movimientos — RF-1
 * 7 columnas fijas fecha|producto|proveedor|tipo|cantidad|motivo|id, "—" para null, sin fetch.
 */
export default function MovimientosHistorial({ movimientos = [] }) {
  return (
    <table className="w-full divide-y divide-neutral-200">
      <thead>
        <tr>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Fecha</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Producto</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Proveedor</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Tipo</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Cantidad</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Motivo</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">ID</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-neutral-200">
        {movimientos.map((m) => (
          <tr key={m.id} data-testid={`movimiento-fila-${m.id}`} className="hover:bg-neutral-50">
            <td className="p-3 text-sm border-t border-neutral-200">{m.fecha}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{m.producto_codigo}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{m.proveedor_codigo ?? '—'}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{m.tipo}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{m.cantidad}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{m.motivo ?? '—'}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{m.id}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
