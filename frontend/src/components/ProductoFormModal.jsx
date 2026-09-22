import React, { useState, useEffect } from 'react';

/**
 * Modal de alta/edición de producto — RF-2, RF-3
 * Valida solo presencia tras trim, sin fetch, SKU deshabilitado en edición.
 */
export default function ProductoFormModal({ modo = 'alta', producto, onSubmit, onClose, cargando = false, errorApi }) {
  const esEdicion = modo === 'edicion';
  const [nombre, setNombre] = useState('');
  const [sku, setSku] = useState('');
  const [categoria, setCategoria] = useState('');
  const [stock, setStock] = useState('');
  const [errores, setErrores] = useState({});

  useEffect(() => {
    if (esEdicion && producto) {
      setNombre(producto.nombre || '');
      setSku(producto.sku || '');
      setCategoria(producto.categoria || '');
      setStock('');
    } else {
      setNombre('');
      setSku('');
      setCategoria('');
      setStock('');
    }
    setErrores({});
  }, [esEdicion, producto]);

  const validar = () => {
    const err = {};
    if (!nombre.trim()) err.nombre = 'Nombre requerido';
    if (!sku.trim()) err.sku = 'SKU requerido';
    if (!categoria) err.categoria = 'Categoría requerida';
    // stock opcional, si informado debe ser entero >=0 (forma básica)
    if (stock !== '' && stock !== null && stock !== undefined) {
      const n = Number(stock);
      if (!Number.isInteger(n) || n < 0) err.stock = 'Stock debe ser entero ≥0';
    }
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
    if (esEdicion) {
      onSubmit?.({ nombre: nombre.trim(), categoria });
    } else {
      const payload = { nombre: nombre.trim(), sku: sku.trim(), categoria };
      if (stock !== '' && stock !== null && stock !== undefined) {
        // stock vacío → ausencia (no enviar)
        const n = Number(stock);
        if (!Number.isNaN(n)) payload.stock_inicial = n;
      }
      onSubmit?.(payload);
    }
  };

  return (
    <div className="fixed inset-0 bg-neutral-900/50 flex items-center justify-center p-4">
      <div role="dialog" aria-modal="true" className="bg-neutral-0 rounded-lg p-6 flex flex-col gap-4 w-full max-w-md">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <label htmlFor="producto-nombre" className="text-sm font-medium text-neutral-700">Nombre</label>
            <input id="producto-nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} className={errores.nombre ? "bg-neutral-0 border border-error-600 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full" : "bg-neutral-0 border border-neutral-200 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full"} />
            {errores.nombre && <span className="text-sm text-error-600">{errores.nombre}</span>}
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="producto-sku" className="text-sm font-medium text-neutral-700">SKU</label>
            <input id="producto-sku" value={sku} onChange={(e) => setSku(e.target.value)} disabled={esEdicion} className={errores.sku ? "bg-neutral-0 border border-error-600 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full disabled:bg-neutral-100" : "bg-neutral-0 border border-neutral-200 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full disabled:bg-neutral-100"} />
            {errores.sku && <span className="text-sm text-error-600">{errores.sku}</span>}
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="producto-categoria" className="text-sm font-medium text-neutral-700">Categoría</label>
            <select id="producto-categoria" value={categoria} onChange={(e) => setCategoria(e.target.value)} className={errores.categoria ? "bg-neutral-0 border border-error-600 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full" : "bg-neutral-0 border border-neutral-200 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full"}>
              <option value="">Seleccione</option>
              <option value="videojuego">videojuego</option>
              <option value="consola">consola</option>
              <option value="accesorio">accesorio</option>
            </select>
            {errores.categoria && <span className="text-sm text-error-600">{errores.categoria}</span>}
          </div>
          {!esEdicion && (
            <div className="flex flex-col gap-1">
              <label htmlFor="producto-stock" className="text-sm font-medium text-neutral-700">Stock inicial</label>
              <input id="producto-stock" type="number" value={stock} onChange={(e) => setStock(e.target.value)} className={errores.stock ? "bg-neutral-0 border border-error-600 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full" : "bg-neutral-0 border border-neutral-200 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none w-full"} />
              {errores.stock && <span className="text-sm text-error-600">{errores.stock}</span>}
            </div>
          )}
          {errorApi && <div role="alert" className="text-sm text-error-600">{errorApi.mensaje || errorApi}</div>}
          <div className="flex gap-4 justify-end">
            <button type="submit" disabled={cargando} className="bg-primary-500 text-white hover:bg-primary-600 focus:ring-2 focus:ring-primary-500 focus:outline-none px-4 py-2 rounded text-sm font-semibold disabled:bg-primary-300 disabled:cursor-not-allowed">
              {esEdicion ? 'Guardar' : 'Crear'}
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
