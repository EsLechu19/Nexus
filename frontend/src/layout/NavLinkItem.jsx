import React from 'react';
import { NavLink } from 'react-router-dom';

/**
 * Enlace de navegación con marcado activo.
 * RF-1: marca visual + aria-current="page" y anillo de foco.
 */
export default function NavLinkItem({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `px-3 py-2 rounded text-sm focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 ${
          isActive ? 'text-primary-600 font-semibold' : 'text-neutral-700 font-normal'
        }`
      }
    >
      {children}
    </NavLink>
  );
}
