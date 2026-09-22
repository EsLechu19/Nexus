import React, { useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

/**
 * Header con título y botón Cerrar sesión condicional — RF-5.
 * Solo visible cuando isAuthenticated, nunca en /login (Login está fuera de AppLayout).
 * Sin confirmación, doble click ignorado.
 */
export default function Header() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const navegandoRef = useRef(false);

  const handleLogout = () => {
    if (navegandoRef.current) return;
    navegandoRef.current = true;
    logout();
    navigate('/login', { state: { mensaje: 'Sesión cerrada correctamente' }, replace: true });
    // reset después de navegación para permitir futuros logouts tras nuevo login
    setTimeout(() => {
      navegandoRef.current = false;
    }, 300);
  };

  return (
    <header className="bg-neutral-0 border-b border-neutral-200 p-6 flex justify-between items-center" role="banner">
      <h1 className="text-xl font-semibold text-neutral-900">Nexus — Gestión de Inventario</h1>
      {isAuthenticated && (
        <button
          type="button"
          onClick={handleLogout}
          className="bg-neutral-200 text-neutral-900 hover:bg-neutral-300 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-medium"
        >
          Cerrar sesión
        </button>
      )}
    </header>
  );
}
