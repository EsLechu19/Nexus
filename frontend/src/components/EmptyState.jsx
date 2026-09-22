import React from 'react';

/**
 * Estado vacío — RF-5.
 * Mensaje por defecto "Sin datos disponibles", sin botón, diferenciado de error/cargando.
 */
export default function EmptyState({ mensaje = 'Sin datos disponibles', descripcion }) {
  return (
    <div className="bg-neutral-0 border border-neutral-200 p-6 rounded flex flex-col gap-4 font-sans text-neutral-700">
      <p>{mensaje}</p>
      {descripcion && <p>{descripcion}</p>}
    </div>
  );
}
