import React, { useState, useEffect } from 'react';
import useProveedores from '../hooks/useProveedores.js';
import { crearProveedor, editarProveedor, bajaProveedor } from '../api/proveedores.js';
import ProveedorTabla from '../components/ProveedorTabla.jsx';
import ProveedorFormModal from '../components/ProveedorFormModal.jsx';
import ProveedorBajaDialog from '../components/ProveedorBajaDialog.jsx';
import Loading from '../components/Loading.jsx';
import EmptyState from '../components/EmptyState.jsx';
import ErrorMessage from '../components/ErrorMessage.jsx';

/**
 * Página de proveedores — RF-1..5
 * Orquesta listado, alta, edición y baja con revalidación.
 */
export default function Proveedores() {
  const { proveedores, cargandoListado, errorListado, revalidar } = useProveedores();
  const [modal, setModal] = useState({ abierto: false, modo: 'alta', proveedor: null });
  const [dialogoBaja, setDialogoBaja] = useState({ abierto: false, proveedor: null });
  const [operacion, setOperacion] = useState({ tipo: null, cargando: false, error: null });
  const [mensajeExito, setMensajeExito] = useState(null);
  const [ultimoPayload, setUltimoPayload] = useState(null);

  useEffect(() => {
    if (mensajeExito) {
      const t = setTimeout(() => setMensajeExito(null), 3000);
      return () => clearTimeout(t);
    }
  }, [mensajeExito]);

  const abrirAlta = () => {
    setOperacion({ tipo: null, cargando: false, error: null });
    setModal({ abierto: true, modo: 'alta', proveedor: null });
  };

  const abrirEdicion = (proveedor) => {
    setOperacion({ tipo: null, cargando: false, error: null });
    setModal({ abierto: true, modo: 'edicion', proveedor });
  };

  const abrirBaja = (proveedor) => {
    setOperacion({ tipo: null, cargando: false, error: null });
    setDialogoBaja({ abierto: true, proveedor });
  };

  const cerrarModal = () => {
    if (operacion.cargando) return;
    setModal({ abierto: false, modo: 'alta', proveedor: null });
    setOperacion({ tipo: null, cargando: false, error: null });
  };

  const cerrarBaja = () => {
    if (operacion.cargando) return;
    setDialogoBaja({ abierto: false, proveedor: null });
    setOperacion({ tipo: null, cargando: false, error: null });
  };

  const handleCrear = async (payload) => {
    setUltimoPayload(payload);
    setOperacion({ tipo: 'alta', cargando: true, error: null });
    try {
      await crearProveedor(payload);
      setModal({ abierto: false, modo: 'alta', proveedor: null });
      setMensajeExito('Proveedor creado correctamente');
      await revalidar();
    } catch (e) {
      setOperacion({ tipo: 'alta', cargando: false, error: e });
      return;
    }
    setOperacion({ tipo: null, cargando: false, error: null });
  };

  const handleEditar = async (payload) => {
    const codigo = modal.proveedor?.codigo;
    setUltimoPayload(payload);
    setOperacion({ tipo: 'edicion', cargando: true, error: null });
    try {
      await editarProveedor(codigo, payload);
      setModal({ abierto: false, modo: 'alta', proveedor: null });
      setMensajeExito('Proveedor actualizado correctamente');
      await revalidar();
    } catch (e) {
      setOperacion({ tipo: 'edicion', cargando: false, error: e });
      return;
    }
    setOperacion({ tipo: null, cargando: false, error: null });
  };

  const handleBajaConfirmar = async () => {
    const codigo = dialogoBaja.proveedor?.codigo;
    setOperacion({ tipo: 'baja', cargando: true, error: null });
    try {
      await bajaProveedor(codigo);
      setDialogoBaja({ abierto: false, proveedor: null });
      setMensajeExito('Proveedor dado de baja correctamente');
      await revalidar();
    } catch (e) {
      setOperacion({ tipo: 'baja', cargando: false, error: e });
      return;
    }
    setOperacion({ tipo: null, cargando: false, error: null });
  };

  const handleReintentar = async () => {
    if (!ultimoPayload) return;
    if (operacion.tipo === 'alta') await handleCrear(ultimoPayload);
    else if (operacion.tipo === 'edicion') await handleEditar(ultimoPayload);
  };

  const handleReintentarBaja = async () => {
    await handleBajaConfirmar();
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
    if (proveedores.length === 0) return <EmptyState mensaje="Sin datos disponibles" />;
    return <ProveedorTabla proveedores={proveedores} onEditar={abrirEdicion} onBaja={abrirBaja} />;
  };

  const esEdicion = modal.modo === 'edicion';

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-semibold text-neutral-900">Proveedores</h2>
      <button type="button" onClick={abrirAlta} className="bg-primary-500 text-white hover:bg-primary-600 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-primary-300 disabled:cursor-not-allowed self-start">
        Crear proveedor
      </button>
      {mensajeExito && <div role="status" aria-live="polite" className="bg-success-50 border border-success-600 text-success-600 p-4 rounded text-sm font-sans">{mensajeExito}</div>}
      {renderContenido()}
      {modal.abierto && (
        <ProveedorFormModal
          modo={modal.modo}
          proveedor={modal.proveedor}
          onSubmit={esEdicion ? handleEditar : handleCrear}
          onClose={cerrarModal}
          cargando={operacion.cargando}
          errorApi={operacion.error}
          onReintentar={handleReintentar}
        />
      )}
      {dialogoBaja.abierto && (
        <ProveedorBajaDialog
          proveedor={dialogoBaja.proveedor}
          onConfirmar={handleBajaConfirmar}
          onCancelar={cerrarBaja}
          cargando={operacion.cargando}
          errorApi={operacion.error}
        />
      )}
    </div>
  );
}
