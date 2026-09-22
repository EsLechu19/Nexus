import { useState, useCallback, useEffect } from 'react';
import { listarProveedores } from '../api/proveedores.js';

/**
 * Hook para listado de proveedores — RF-1, RF-5
 * Estado solo en memoria, revalida siempre GET tras mutación, sin persistencia.
 */
export default function useProveedores() {
  const [proveedores, setProveedores] = useState([]);
  const [cargandoListado, setCargandoListado] = useState(false);
  const [errorListado, setErrorListado] = useState(null);

  const revalidar = useCallback(async () => {
    setCargandoListado(true);
    setErrorListado(null);
    try {
      const data = await listarProveedores();
      setProveedores(Array.isArray(data) ? data : []);
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

  return { proveedores, cargandoListado, errorListado, revalidar };
}
