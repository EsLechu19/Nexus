import React from 'react';

/**
 * Página 404 — ruta inexistente.
 * RF-2: mensaje en español sin romper layout.
 */
export default function NotFoundPage() {
  return (
    <div>
      <h2>404 — Página no encontrada</h2>
      <p>La ruta solicitada no existe.</p>
    </div>
  );
}
