import React, { useState, useEffect, useRef } from 'react';
import useMovimientos from '../hooks/useMovimientos.js';
import { crearEntrada, crearSalida } from '../api/movimientos.js';
import MovimientosHistorial from '../components/MovimientosHistorial.jsx';
import MovimientoFormModal from '../components/MovimientoFormModal.jsx';
import Loading from '../components/Loading.jsx';
import EmptyState from '../components/EmptyState.jsx';
import ErrorMessage from '../components/ErrorMessage.jsx';

/**
 * Página de movimientos — RF-1, RF-2, RF-4
 * Historial en solo lectura + alta de entrada/salida con revalidación uniforme (RF-4).
 * RF-4: banner éxito 3s separado de ErrorMessage, revalidación GET completo coexistiendo con error,
 * 401 como validacion sin Reintentar, sin persistencia cliente, múltiples clics solo una petición.
 */
export default function Movimientos() {
  const { movimientos, productos, proveedores, cargandoHistorial, cargandoSelects, errorHistorial, errorSelects, revalidar, cargarSelects } = useMovimientos();
  const [modalAbierto, setModalAbierto] = useState(false);
  const [operacion, setOperacion] = useState({ tipo: null, cargando: false, error: null });
  const [mensajeExito, setMensajeExito] = useState(null);
  const [ultimoPayload, setUltimoPayload] = useState(null);
  const timeoutExitoRef = useRef(null);
  const cargandoAltaRef = useRef(false);

  // Banner éxito 3s: reinicia timer si ya existe banner previo (mismo mensaje)
  const mostrarExito = (msg) => {
    setMensajeExito(msg);
    if (timeoutExitoRef.current) clearTimeout(timeoutExitoRef.current);
    timeoutExitoRef.current = setTimeout(() => setMensajeExito(null), 3000);
  };

  useEffect(() => {
    return () => {
      if (timeoutExitoRef.current) clearTimeout(timeoutExitoRef.current);
    };
  }, []);

  const abrirAlta = () => {
    setOperacion({ tipo: null, cargando: false, error: null });
    setModalAbierto(true);
  };

  const cerrarModal = () => {
    if (operacion.cargando || cargandoAltaRef.current) return;
    setModalAbierto(false);
    setOperacion({ tipo: null, cargando: false, error: null });
  };

  const handleCrear = async (payload) => {
    // RF-4: evitar duplicados locales por múltiples clics rápidos (ref sincrónico evita race por closure)
    if (cargandoAltaRef.current) return;
    cargandoAltaRef.current = true;
    setUltimoPayload(payload);
    setOperacion({ tipo: 'alta', cargando: true, error: null });
    try {
      if (payload.proveedor_codigo) {
        await crearEntrada(payload);
      } else {
        await crearSalida(payload);
      }
      setModalAbierto(false);
      mostrarExito('Movimiento registrado correctamente');
      // RF-4: revalidación siempre GET completo, sin persistencia; si falla mantiene éxito y muestra error debajo
      await revalidar();
    } catch (e) {
      cargandoAltaRef.current = false;
      setOperacion({ tipo: 'alta', cargando: false, error: e });
      return;
    }
    cargandoAltaRef.current = false;
    setOperacion({ tipo: null, cargando: false, error: null });
  };

  const handleReintentarAlta = async () => {
    if (cargandoAltaRef.current) return;
    if (ultimoPayload) await handleCrear(ultimoPayload);
  };

  const renderContenido = () => {
    if (cargandoHistorial) return <Loading mensaje="Cargando..." />;
    if (errorHistorial) {
      const esConexion = errorHistorial.tipo === 'conexion';
      return (
        <ErrorMessage
          mensaje={errorHistorial.mensaje}
          variante={esConexion ? 'conexion' : 'validacion'}
          onReintentar={esConexion ? revalidar : undefined}
          cargando={cargandoHistorial}
        />
      );
    }
    if (movimientos.length === 0) return <EmptyState mensaje="Sin datos disponibles" />;
    return <MovimientosHistorial movimientos={movimientos} />;
  };

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-semibold text-neutral-900">Movimientos</h2>
      <button type="button" onClick={abrirAlta} className="bg-primary-500 text-white hover:bg-primary-600 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-primary-300 disabled:cursor-not-allowed self-start">
        Crear movimiento
      </button>
      {mensajeExito && <div role="status" aria-live="polite" className="bg-success-50 border border-success-600 text-success-600 p-4 rounded text-sm font-sans">{mensajeExito}</div>}
      {renderContenido()}
      {modalAbierto && (
        <MovimientoFormModal
          productos={productos}
          proveedores={proveedores}
          cargandoSelects={cargandoSelects}
          errorSelects={errorSelects}
          onReintentarSelects={cargarSelects}
          onSubmit={handleCrear}
          onClose={cerrarModal}
          cargando={operacion.cargando}
          errorApi={operacion.error}
          onReintentar={handleReintentarAlta}
        />
      )}
    </div>
  );
}
