import React, { useState, useEffect } from 'react';
import useProductos from '../hooks/useProductos.js';
import { crearProducto, editarProducto, bajaProducto } from '../api/productos.js';
import ProductoTabla from '../components/ProductoTabla.jsx';
import ProductoFormModal from '../components/ProductoFormModal.jsx';
import ProductoBajaDialog from '../components/ProductoBajaDialog.jsx';
import Loading from '../components/Loading.jsx';
import EmptyState from '../components/EmptyState.jsx';
import ErrorMessage from '../components/ErrorMessage.jsx';

/**
 * Página de productos — RF-1..5
 * Orquesta listado, alta, edición, baja y revalidación sin caché.
 */
export default function Productos() {
  const { productos, cargandoListado, errorListado, revalidar } = useProductos();
  const [modal, setModal] = useState({ abierto: false, modo: 'alta', producto: null });
  const [dialogoBaja, setDialogoBaja] = useState({ abierto: false, producto: null });
  const [operacion, setOperacion] = useState({ tipo: null, cargando: false, error: null });
  const [mensajeExito, setMensajeExito] = useState(null);

  useEffect(() => {
    if (mensajeExito) {
      const t = setTimeout(() => setMensajeExito(null), 3000);
      return () => clearTimeout(t);
    }
  }, [mensajeExito]);

  const abrirAlta = () => {
    setOperacion({ tipo: null, cargando: false, error: null });
    setModal({ abierto: true, modo: 'alta', producto: null });
  };

  const abrirEdicion = (producto) => {
    // defensivo: si inactivo, no abrir (pero listado solo muestra activos)
    setOperacion({ tipo: null, cargando: false, error: null });
    setModal({ abierto: true, modo: 'edicion', producto });
  };

  const abrirBaja = (producto) => {
    setOperacion({ tipo: null, cargando: false, error: null });
    setDialogoBaja({ abierto: true, producto });
  };

  const cerrarModal = () => {
    if (operacion.cargando) return;
    setModal({ abierto: false, modo: 'alta', producto: null });
    setOperacion({ tipo: null, cargando: false, error: null });
  };

  const cerrarBaja = () => {
    if (operacion.cargando) return;
    setDialogoBaja({ abierto: false, producto: null });
    setOperacion({ tipo: null, cargando: false, error: null });
  };

  const handleCrear = async (payload) => {
    setOperacion({ tipo: 'alta', cargando: true, error: null });
    try {
      await crearProducto(payload);
      setModal({ abierto: false, modo: 'alta', producto: null });
      setMensajeExito('Producto creado correctamente');
      await revalidar();
    } catch (e) {
      setOperacion({ tipo: 'alta', cargando: false, error: e });
      return;
    }
    setOperacion({ tipo: null, cargando: false, error: null });
  };

  const handleEditar = async (payload) => {
    const sku = modal.producto?.sku;
    setOperacion({ tipo: 'edicion', cargando: true, error: null });
    try {
      await editarProducto(sku, payload);
      setModal({ abierto: false, modo: 'alta', producto: null });
      setMensajeExito('Producto actualizado correctamente');
      await revalidar();
    } catch (e) {
      setOperacion({ tipo: 'edicion', cargando: false, error: e });
      return;
    }
    setOperacion({ tipo: null, cargando: false, error: null });
  };

  const handleBajaConfirmar = async () => {
    const sku = dialogoBaja.producto?.sku;
    setOperacion({ tipo: 'baja', cargando: true, error: null });
    try {
      await bajaProducto(sku);
      setDialogoBaja({ abierto: false, producto: null });
      setMensajeExito('Producto dado de baja correctamente');
      await revalidar();
    } catch (e) {
      setOperacion({ tipo: 'baja', cargando: false, error: e });
      return;
    }
    setOperacion({ tipo: null, cargando: false, error: null });
  };

  const renderContenido = () => {
    if (cargandoListado) return <Loading mensaje="Cargando..." />;
    if (errorListado) {
      const esConexion = errorListado.tipo === 'conexion';
      return (
        <ErrorMessage
          mensaje={errorListado.mensaje}
          variante={esConexion ? 'conexion' : 'validacion'}
          onReintentar={esConexion ? revalidar : undefined}
          cargando={cargandoListado}
        />
      );
    }
    if (productos.length === 0) return <EmptyState mensaje="Sin datos disponibles" />;
    return <ProductoTabla productos={productos} onEditar={abrirEdicion} onBaja={abrirBaja} />;
  };

  const errorOperacion = operacion.error;
  const esErrorConexion = errorOperacion?.tipo === 'conexion';

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-semibold text-neutral-900">Productos</h2>
      <button type="button" onClick={abrirAlta} className="bg-primary-500 text-white hover:bg-primary-600 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-primary-300 disabled:cursor-not-allowed self-start">
        Crear producto
      </button>
      {mensajeExito && <div role="status" aria-live="polite" className="bg-success-50 border border-success-600 text-success-600 p-4 rounded text-sm font-sans">{mensajeExito}</div>}
      {renderContenido()}
      {modal.abierto && (
        <ProductoFormModal
          modo={modal.modo}
          producto={modal.producto}
          onSubmit={modal.modo === 'alta' ? handleCrear : handleEditar}
          onClose={cerrarModal}
          cargando={operacion.cargando}
          errorApi={operacion.error}
        />
      )}
      {dialogoBaja.abierto && (
        <ProductoBajaDialog
          producto={dialogoBaja.producto}
          onConfirmar={handleBajaConfirmar}
          onCancelar={cerrarBaja}
          cargando={operacion.cargando}
          errorApi={operacion.error}
        />
      )}
      {/* Error de operación dentro de modal/diálogo ya se muestra vía prop errorApi; si revalidación falla, se muestra vía errorListado manteniendo éxito */}
    </div>
  );
}
