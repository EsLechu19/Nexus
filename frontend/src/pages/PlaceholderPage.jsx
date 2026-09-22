import React from 'react';

/**
 * Placeholder uniforme para secciones en construcción (T04 stub).
 * RF-2: incluye nombre de sección + "En construcción" y mantiene layout.
 * Será enriquecido en T13 con props adicionales si hace falta.
 */
export default function PlaceholderPage({ nombreSeccion }) {
  return (
    <div>
      <h2>{nombreSeccion} — En construcción</h2>
      <p>Esta sección estará disponible próximamente.</p>
    </div>
  );
}
