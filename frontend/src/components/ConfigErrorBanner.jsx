import React from 'react';

/**
 * Banner de error global por configuración/API no disponible — RF-4.
 * Mantiene nav visible (no lo renderiza), suprime Outlet a nivel AppLayout.
 * Botón Reintentar sin reload, deshabilitado mientras cargando.
 */
export default function ConfigErrorBanner({ mensaje = 'Error de conexión con el servidor', onReintentar, cargando = false }) {
  return (
    <div role="alert" aria-live="assertive" aria-busy={cargando ? 'true' : 'false'} className="bg-error-50 border border-error-100 text-error-700 p-4 rounded flex flex-col gap-4 font-sans">
      <p>{mensaje}</p>
      <button type="button" onClick={onReintentar} disabled={cargando} aria-label="Reintentar" className="bg-white text-neutral-700 border border-neutral-200 hover:bg-neutral-50 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-neutral-100 disabled:cursor-not-allowed self-start">
        Reintentar
      </button>
    </div>
  );
}
