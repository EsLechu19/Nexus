import React from 'react';

/**
 * Diálogo de confirmación de baja lógica — RF-4
 * Sin fetch, sin persistencia.
 */
export default function ProductoBajaDialog({ producto, onConfirmar, onCancelar, cargando = false, errorApi }) {
  if (!producto) return null;
  return (
    <div className="fixed inset-0 bg-neutral-900/50 flex items-center justify-center p-4">
      <div role="dialog" aria-modal="true" className="bg-neutral-0 rounded-lg p-6 flex flex-col gap-4 w-full max-w-md">
        <p className="text-sm text-neutral-700">
          ¿Dar de baja a {producto.nombre} ({producto.sku})? No se puede deshacer desde este MVP
        </p>
        {errorApi && <div role="alert" className="text-sm text-error-600">{errorApi.mensaje || errorApi}</div>}
        <div className="flex gap-4 justify-end">
          <button type="button" onClick={onConfirmar} disabled={cargando} className="bg-error-600 text-white hover:bg-error-700 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-error-300 disabled:cursor-not-allowed">
            Confirmar
          </button>
          <button type="button" onClick={onCancelar} className="bg-white text-neutral-700 border border-neutral-200 hover:bg-neutral-50 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-neutral-100 disabled:cursor-not-allowed">
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
