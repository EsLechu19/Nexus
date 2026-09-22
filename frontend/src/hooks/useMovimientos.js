import { useState, useCallback, useEffect } from 'react';
import { listarMovimientos } from '../api/movimientos.js';
import { listarProductos } from '../api/productos.js';
import { listarProveedores } from '../api/proveedores.js';

/**
 * Hook para historial de movimientos y selects de productos/proveedores — RF-1, RF-4
 * Estado solo en memoria, revalida siempre GET historial completo tras alta, sin persistencia.
 */
export default function useMovimientos() {
  const [movimientos, setMovimientos] = useState([]);
  const [productos, setProductos] = useState([]);
  const [proveedores, setProveedores] = useState([]);
  const [cargandoHistorial, setCargandoHistorial] = useState(false);
  const [cargandoSelects, setCargandoSelects] = useState(false);
  const [errorHistorial, setErrorHistorial] = useState(null);
  const [errorSelects, setErrorSelects] = useState(null);

  const revalidar = useCallback(async () => {
    setCargandoHistorial(true);
    setErrorHistorial(null);
    try {
      const data = await listarMovimientos();
      setMovimientos(Array.isArray(data) ? data : []);
      setErrorHistorial(null);
    } catch (e) {
      setErrorHistorial(e);
    } finally {
      setCargandoHistorial(false);
    }
  }, []);

  const cargarSelects = useCallback(async () => {
    setCargandoSelects(true);
    setErrorSelects(null);
    try {
      const [prodData, provData] = await Promise.all([listarProductos(), listarProveedores()]);
      setProductos(Array.isArray(prodData) ? prodData : []);
      setProveedores(Array.isArray(provData) ? provData : []);
      setErrorSelects(null);
    } catch (e) {
      setErrorSelects(e);
    } finally {
      setCargandoSelects(false);
    }
  }, []);

  useEffect(() => {
    revalidar();
  }, [revalidar]);

  useEffect(() => {
    cargarSelects();
  }, [cargarSelects]);

  return {
    movimientos,
    productos,
    proveedores,
    cargandoHistorial,
    cargandoSelects,
    errorHistorial,
    errorSelects,
    revalidar,
    cargarSelects,
  };
}
