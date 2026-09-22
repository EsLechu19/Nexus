import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import NavLinkItem from './NavLinkItem.jsx';
import ConfigErrorBanner from '../components/ConfigErrorBanner.jsx';
import Header from './Header.jsx';
import { esConfigValida } from '../api/client.js';

/**
 * Layout persistente del esqueleto base.
 * RF-1: header + nav siempre visible con 4 secciones y main con Outlet.
 * RF-4: muestra banner global si config inválida y suprime Outlet (prioridad RF-2 vs RF-4).
 */
export default function AppLayout() {
  const [hasError, setHasError] = useState(() => !esConfigValida());
  const [cargando, setCargando] = useState(false);

  const handleReintentar = () => {
    if (cargando) return;
    setCargando(true);
    // revalida sin reload, preserva ruta/historial
    setTimeout(() => {
      const ok = esConfigValida();
      setHasError(!ok);
      setCargando(false);
    }, 0);
  };

  return (
    <div className="font-sans bg-neutral-0 text-neutral-900 min-h-screen">
      <Header />
      <nav aria-label="Navegación principal" className="bg-neutral-0 border-b border-neutral-200 p-4">
        <ul className="flex gap-4">
          <li>
            <NavLinkItem to="/productos">Productos</NavLinkItem>
          </li>
          <li>
            <NavLinkItem to="/proveedores">Proveedores</NavLinkItem>
          </li>
          <li>
            <NavLinkItem to="/movimientos">Movimientos</NavLinkItem>
          </li>
          <li>
            <NavLinkItem to="/stock">Stock</NavLinkItem>
          </li>
        </ul>
      </nav>
      {hasError ? (
        <ConfigErrorBanner
          mensaje="Error de conexión con el servidor"
          onReintentar={handleReintentar}
          cargando={cargando}
        />
      ) : null}
      <main id="contenido-principal" className="p-6 flex flex-col gap-4">
        {hasError ? null : <Outlet />}
      </main>
    </div>
  );
}
