import { useState, useCallback, useEffect } from 'react';
import { listarStock } from '../api/stock.js';

/**
 * Valida fila de stock antes de render — RF-1
 * Verifica tipos y presencia de codigo, nombre, stock_actual, stock_minimo, alerta.
 * Si falta alguno o tipo incorrecto, la fila se omite.
 */
export function esFilaStockValida(f) {
  if (!f || typeof f !== 'object') return false;
  if (typeof f.codigo !== 'string' || f.codigo.trim() === '') return false;
  if (typeof f.nombre !== 'string' || f.nombre.trim() === '') return false;
  if (!Number.isInteger(f.stock_actual)) return false;
  if (!Number.isInteger(f.stock_minimo)) return false;
  if (typeof f.alerta !== 'boolean') return false;
  return true;
}

/**
 * Hook para listado de stock — RF-1, RF-2
 * Estado solo en memoria, sin persistencia cliente, revalida siempre GET completo.
 * Filtra filas corruptas sin romper resto (todas corruptas → []).
 */
export default function useStock() {
  const [stock, setStock] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);

  const revalidar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const data = await listarStock();
      if (!Array.isArray(data)) {
        setStock([]);
      } else {
        const filtradas = data.filter(esFilaStockValida);
        setStock(filtradas);
      }
      setError(null);
    } catch (e) {
      setError(e);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    revalidar();
  }, [revalidar]);

  return { stock, cargando, error, revalidar };
}
