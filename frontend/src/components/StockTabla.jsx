import React from 'react';

/**
 * Tabla presentacional de stock — RF-1
 * 5 columnas fijas codigo|nombre|stock_actual|stock_minimo|alerta, badge y fila marcada si alerta==true.
 * Recibe stock ya depurado por props, sin fetch, sin ordenar.
 * Manejo defensivo: omite filas corruptas sin inventar valores, ignora campos extra.
 */
function esFilaValida(f) {
  if (!f || typeof f !== 'object') return false;
  if (typeof f.codigo !== 'string' || f.codigo.trim() === '') return false;
  if (typeof f.nombre !== 'string' || f.nombre.trim() === '') return false;
  if (!Number.isInteger(f.stock_actual)) return false;
  if (!Number.isInteger(f.stock_minimo)) return false;
  if (typeof f.alerta !== 'boolean') return false;
  return true;
}

// Mapeos literales para purga segura de Tailwind (RNF-7) — todas las combinaciones escritas literalmente, sin concatenación
const alertaBadge = {
  true: "bg-alerta-100 text-alerta-600 border border-alerta-100",
  false: "text-neutral-700",
};
const filaStock = {
  true: "bg-alerta-50",
  false: "",
};
const boton = {
  primario: "bg-primary-500 text-white hover:bg-primary-600 focus:ring-primary-500",
  secundario: "bg-white text-neutral-700 border border-neutral-200 hover:bg-neutral-50",
  peligro: "bg-error-600 text-white hover:bg-error-700 focus:ring-error-600",
};

export default function StockTabla({ stock = [] }) {
  const filasValidas = stock.filter(esFilaValida);
  return (
    <table className="w-full divide-y divide-neutral-200">
      <thead>
        <tr>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Codigo</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Nombre</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Stock actual</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Stock minimo</th>
          <th className="bg-neutral-100 text-neutral-700 font-medium text-xs uppercase p-3 text-left">Alerta</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-neutral-200">
        {filasValidas.map((s) => (
          <tr
            key={`${s.codigo}-${s.nombre}`}
            data-testid={`stock-fila-${s.codigo}`}
            data-alerta={s.alerta ? 'true' : 'false'}
            className={`${filaStock[s.alerta]} hover:bg-neutral-50`}
          >
            <td className="p-3 text-sm border-t border-neutral-200">{s.codigo}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{s.nombre}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{s.stock_actual}</td>
            <td className="p-3 text-sm border-t border-neutral-200">{s.stock_minimo}</td>
            <td className="p-3 text-sm border-t border-neutral-200">
              <span className={alertaBadge[s.alerta]}>{s.alerta ? 'Bajo stock' : '—'}</span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
