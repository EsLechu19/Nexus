import React, { useState } from 'react';
import ErrorMessage from './ErrorMessage.jsx';

/**
 * Modal de alta de movimiento — RF-2, RF-3
 * Selector Entrada|Salida, 4/3 campos condicionados, validación cantidad>0 y motivo no vacío.
 */
export default function MovimientoFormModal({
  productos = [],
  proveedores = [],
  cargandoSelects = false,
  errorSelects = null,
  onReintentarSelects,
  onSubmit,
  onClose,
  cargando = false,
  errorApi = null,
  onReintentar,
}) {
  const [tipo, setTipo] = useState('entrada');
  const [producto, setProducto] = useState('');
  const [proveedor, setProveedor] = useState('');
  const [cantidad, setCantidad] = useState('');
  const [motivo, setMotivo] = useState('');
  const [errores, setErrores] = useState({});

  const esEntrada = tipo === 'entrada';

  const handleTipoChange = (nuevoTipo) => {
    if (nuevoTipo === tipo) return;
    setTipo(nuevoTipo);
    // conservar producto/cantidad/motivo, limpiar proveedor y errores de proveedor
    if (nuevoTipo === 'salida') {
      setProveedor('');
    } else {
      setProveedor('');
    }
    setErrores({});
  };

  const validar = () => {
    const err = {};
    if (!producto.trim()) err.producto = 'Campo requerido';
    if (esEntrada && !proveedor.trim()) err.proveedor = 'Campo requerido';
    if (!cantidad.trim()) {
      err.cantidad = 'Campo requerido';
    } else if (!/^-?\d+$/.test(cantidad.trim()) || !Number.isInteger(Number(cantidad.trim())) || Number(cantidad.trim()) <= 0) {
      err.cantidad = 'Debe ser un número entero mayor a 0';
    }
    if (motivo !== '' && motivo.trim() === '') err.motivo = 'No puede quedar vacío';
    return err;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const err = validar();
    if (Object.keys(err).length > 0) {
      setErrores(err);
      return;
    }
    setErrores({});
    const payload = {
      producto_codigo: producto.trim(),
      cantidad: Number(cantidad.trim()),
    };
    if (esEntrada) {
      payload.proveedor_codigo = proveedor.trim();
    }
    if (motivo.trim() !== '') {
      payload.motivo = motivo.trim();
    }
    onSubmit?.(payload);
  };

  const productosVacios = !cargandoSelects && !errorSelects && productos.length === 0;
  const proveedoresVacios = !cargandoSelects && !errorSelects && proveedores.length === 0 && esEntrada;
  const bloqueaCrear = productosVacios || proveedoresVacios || !!errorSelects;

  return (
    <div className="fixed inset-0 bg-neutral-900/50 flex items-center justify-center p-4">
      <div role="dialog" aria-modal="true" className="bg-neutral-0 rounded-lg p-6 flex flex-col gap-4 w-full max-w-md">
        <div role="tablist" className="flex gap-4">
          <button
            type="button"
            role="tab"
            aria-selected={esEntrada ? 'true' : 'false'}
            onClick={() => handleTipoChange('entrada')}
            className={esEntrada ? "bg-primary-500 text-white hover:bg-primary-600 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-primary-300 disabled:cursor-not-allowed" : "bg-white text-neutral-700 border border-neutral-200 hover:bg-neutral-50 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-neutral-100 disabled:cursor-not-allowed"}
          >
            Entrada
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={!esEntrada ? 'true' : 'false'}
            onClick={() => handleTipoChange('salida')}
            className={!esEntrada ? "bg-primary-500 text-white hover:bg-primary-600 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-primary-300 disabled:cursor-not-allowed" : "bg-white text-neutral-700 border border-neutral-200 hover:bg-neutral-50 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-neutral-100 disabled:cursor-not-allowed"}
          >
            Salida
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <label htmlFor="movimiento-producto" className="text-sm font-medium text-neutral-700">Producto</label>
            <select
              id="movimiento-producto"
              value={producto}
              onChange={(e) => setProducto(e.target.value)}
              disabled={cargandoSelects}
              className={errores.producto ? "bg-neutral-0 border border-error-600 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full" : "bg-neutral-0 border border-neutral-200 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full"}
            >
              <option value="">{cargandoSelects ? 'Cargando...' : 'Selecciona producto'}</option>
              {productos.map((p) => (
                <option key={p.codigo} value={p.codigo}>
                  {p.codigo} — {p.nombre}
                </option>
              ))}
            </select>
            {errores.producto && <span className="text-sm text-error-600">{errores.producto}</span>}
            {productosVacios && <span className="text-sm text-neutral-700">No hay productos activos disponibles. Crea un producto primero.</span>}
          </div>

          {esEntrada && (
            <div className="flex flex-col gap-1">
              <label htmlFor="movimiento-proveedor" className="text-sm font-medium text-neutral-700">Proveedor</label>
              <select
                id="movimiento-proveedor"
                value={proveedor}
                onChange={(e) => setProveedor(e.target.value)}
                disabled={cargandoSelects}
                className={errores.proveedor ? "bg-neutral-0 border border-error-600 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full" : "bg-neutral-0 border border-neutral-200 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full"}
              >
                <option value="">{cargandoSelects ? 'Cargando...' : 'Selecciona proveedor'}</option>
                {proveedores.map((pr) => (
                  <option key={pr.codigo} value={pr.codigo}>
                    {pr.codigo} — {pr.nombre}
                  </option>
                ))}
              </select>
              {errores.proveedor && <span className="text-sm text-error-600">{errores.proveedor}</span>}
              {proveedoresVacios && <span className="text-sm text-neutral-700">No hay proveedores activos disponibles. Crea un proveedor primero.</span>}
            </div>
          )}

          {errorSelects && (
            <ErrorMessage
              mensaje={errorSelects.mensaje || errorSelects.message || String(errorSelects)}
              variante={errorSelects.tipo === 'conexion' ? 'conexion' : 'validacion'}
              onReintentar={errorSelects.tipo === 'conexion' ? onReintentarSelects : undefined}
              cargando={cargandoSelects}
            />
          )}

          {errorApi && (
            <ErrorMessage
              mensaje={errorApi.mensaje || errorApi.message || String(errorApi)}
              variante={errorApi.tipo === 'conexion' ? 'conexion' : 'validacion'}
              onReintentar={errorApi.tipo === 'conexion' ? onReintentar : undefined}
              cargando={cargando}
            />
          )}

          <div className="flex flex-col gap-1">
            <label htmlFor="movimiento-cantidad" className="text-sm font-medium text-neutral-700">Cantidad</label>
            <input
              id="movimiento-cantidad"
              value={cantidad}
              onChange={(e) => setCantidad(e.target.value)}
              className={errores.cantidad ? "bg-neutral-0 border border-error-600 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full" : "bg-neutral-0 border border-neutral-200 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full"}
            />
            {errores.cantidad && <span className="text-sm text-error-600">{errores.cantidad}</span>}
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="movimiento-motivo" className="text-sm font-medium text-neutral-700">Motivo</label>
            <input id="movimiento-motivo" value={motivo} onChange={(e) => setMotivo(e.target.value)} className={errores.motivo ? "bg-neutral-0 border border-error-600 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full" : "bg-neutral-0 border border-neutral-200 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full"} />
            {errores.motivo && <span className="text-sm text-error-600">{errores.motivo}</span>}
          </div>

          <div className="flex gap-4 justify-end">
            <button type="submit" disabled={cargando || bloqueaCrear} className="bg-primary-500 text-white hover:bg-primary-600 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-primary-300 disabled:cursor-not-allowed">
              Crear
            </button>
            <button type="button" onClick={onClose} className="bg-white text-neutral-700 border border-neutral-200 hover:bg-neutral-50 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-neutral-100 disabled:cursor-not-allowed">
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
