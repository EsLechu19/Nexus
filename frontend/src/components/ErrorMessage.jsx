import React from 'react';

/**
 * Estado error por sección — RF-5.
 * Variante conexion: mensaje genérico + botón Reintentar.
 * Variante validacion: mensaje específico sin botón (incl. 401).
 */
export default function ErrorMessage({ mensaje, variante = 'conexion', onReintentar, cargando = false }) {
  const esConexion = variante === 'conexion';
  return (
    <div role="alert" aria-live="assertive" aria-busy={cargando ? 'true' : 'false'} className={esConexion ? "bg-error-50 border border-error-100 text-error-700 p-4 rounded flex flex-col gap-4 font-sans" : "bg-neutral-0 border border-neutral-200 text-neutral-700 p-4 rounded flex flex-col gap-4 font-sans"}>
      <p>{mensaje}</p>
      {esConexion && onReintentar && (
        <button type="button" onClick={onReintentar} disabled={cargando} aria-label="Reintentar" className="bg-white text-neutral-700 border border-neutral-200 hover:bg-neutral-50 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-neutral-100 disabled:cursor-not-allowed self-start">
          Reintentar
        </button>
      )}
      {esConexion && !onReintentar && (
        <button type="button" disabled={cargando} aria-label="Reintentar" className="bg-white text-neutral-700 border border-neutral-200 hover:bg-neutral-50 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-neutral-100 disabled:cursor-not-allowed self-start">
          Reintentar
        </button>
      )}
    </div>
  );
}
