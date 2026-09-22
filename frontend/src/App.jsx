import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './layout/AppLayout.jsx';
import PlaceholderPage from './pages/PlaceholderPage.jsx';
import NotFoundPage from './pages/NotFoundPage.jsx';
import Productos from './pages/Productos.jsx';
import Proveedores from './pages/Proveedores.jsx';
import Movimientos from './pages/Movimientos.jsx';
import Stock from './pages/Stock.jsx';
import Login from './pages/Login.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import { AuthProvider } from './context/AuthContext.jsx';

/**
 * Mapa de rutas — 005 + 013 T05
 * RF-3: /login público fuera de ProtectedRoute, resto bajo guard, guard antes que 404.
 */
export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/productos" replace />} />
            <Route path="/productos" element={<Productos />} />
            <Route path="/proveedores" element={<Proveedores />} />
            <Route path="/movimientos" element={<Movimientos />} />
            <Route path="/stock" element={<Stock />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  );
}
