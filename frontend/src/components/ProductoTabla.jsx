import React from 'react';

/**
 * Tabla presentacional de productos — RF-1
 * 4 columnas fijas, sin filtros, sin fetch.
 */
export default function ProductoTabla({ productos = [], onEditar, onBaja }) {
  return (
    <table className="w-full divide-y divide-neutral-200">
      <thead>
        <tr>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">SKU</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Nombre</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Categoría</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Stock inicial</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Acciones</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-neutral-200">
        {productos.map((p) => (
          <tr key={p.sku} data-testid={`producto-fila-${p.sku}`} className="hover:bg-neutral-50">
            <td className="p-3 text-sm border-t border-neutral-200">{p.sku}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{p.nombre}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{p.categoria}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{p.stock_inicial}</td>
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
