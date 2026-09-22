import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Hook efímero para estado cargando/error/vacío por sección — RF-5, RNF-6.
 * Vive solo en memoria, sin persistencia y sin fetch directo.
 * @param {() => Promise<any>} fetcher - función que retorna datos o lanza error tipado
 */
export default function useApiStatus(fetcher) {
  const [estado, setEstado] = useState('idle');
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(false);
  const isMountedRef = useRef(true);
  const cargandoRef = useRef(false);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const reintentar = useCallback(async () => {
    if (cargandoRef.current) return;
    cargandoRef.current = true;
    setCargando(true);
    setEstado('cargando');
    setError(null);
    try {
      const result = await fetcher();
      if (!isMountedRef.current) return;
      // vacío si array vacío
      if (Array.isArray(result) && result.length === 0) {
        setData(result);
        setEstado('vacio');
      } else {
        setData(result);
        setEstado('exito');
      }
    } catch (e) {
      if (!isMountedRef.current) return;
      setError(e);
      setEstado('error');
    } finally {
      if (isMountedRef.current) {
        setCargando(false);
      }
      cargandoRef.current = false;
    }
  }, [fetcher]);

  return { estado, data, error, cargando, reintentar };
}
