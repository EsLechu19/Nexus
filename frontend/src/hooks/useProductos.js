import { useState, useCallback, useEffect } from 'react';
import { listarProductos } from '../api/productos.js';

/**
 * Hook para listado de productos — RF-1, RF-5
 * Estado solo en memoria, revalida siempre GET tras mutación, sin persistencia.
 */
export default function useProductos() {
  const [productos, setProductos] = useState([]);
  const [cargandoListado, setCargandoListado] = useState(false);
  const [errorListado, setErrorListado] = useState(null);

  const revalidar = useCallback(async () => {
    setCargandoListado(true);
    setErrorListado(null);
    try {
      const data = await listarProductos();
      setProductos(Array.isArray(data) ? data : []);
      setErrorListado(null);
    } catch (e) {
      setErrorListado(e);
    } finally {
      setCargandoListado(false);
    }
  }, []);

  useEffect(() => {
    revalidar();
  }, [revalidar]);

  return { productos, cargandoListado, errorListado, revalidar };
}
