import React from 'react';

/**
 * Estado cargando uniforme — RF-5.
 * Presentacional, sin fetch.
 */
export default function Loading({ mensaje = 'Cargando...', ariaLive = 'polite' }) {
  return (
    <div role="status" aria-live={ariaLive} aria-busy="true" className="text-neutral-700 p-4 font-sans">
      <span>{mensaje}</span>
    </div>
  );
}
