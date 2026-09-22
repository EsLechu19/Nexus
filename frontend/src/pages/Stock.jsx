import React from 'react';
import useStock from '../hooks/useStock.js';
import StockTabla from '../components/StockTabla.jsx';
import Loading from '../components/Loading.jsx';
import EmptyState from '../components/EmptyState.jsx';
import ErrorMessage from '../components/ErrorMessage.jsx';

/**
 * Página de stock — RF-1, RF-2
 * Consulta global en solo lectura con alerta visual, sin filtros/paginación.
 */
export default function Stock() {
  const { stock, cargando, error, revalidar } = useStock();

  const renderContenido = () => {
    if (cargando) return <Loading mensaje="Cargando..." />;
    if (error) {
      const esConexion = error.tipo === 'conexion';
      return (
        <ErrorMessage
          mensaje={error.mensaje}
          variante={esConexion ? 'conexion' : 'validacion'}
          onReintentar={esConexion ? revalidar : undefined}
          cargando={cargando}
        />
      );
    }
    if (stock.length === 0) return <EmptyState mensaje="Sin datos disponibles" />;
    return <StockTabla stock={stock} />;
  };

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-semibold text-neutral-900">Stock</h2>
      {renderContenido()}
    </div>
  );
}
