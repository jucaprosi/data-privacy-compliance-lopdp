"use client";
// ¤adpa ¤frontend-ide
/**
 * BIB-305: indicadores verificables. Cada indicador va por separado (sin cifra única ni porcentaje
 * global), con fecha de corte, denominador, exclusiones y estados sin mapear, y abre sus registros de origen.
 * Si la carga falla no se muestra nada (sin role="alert": la pestaña sigue usable).
 */
import React from "react";
import {
  NOMBRES_CATEGORIA, obtenerIndicadores, registrosDeIndicador,
  type Indicador, type Indicadores, type RegistrosIndicador,
} from "@/lib/biblioteca/indicadores";

const fecha = (iso: string) => new Date(iso).toLocaleString("es-EC", { dateStyle: "medium", timeStyle: "short" });

function TarjetaIndicador({ indicador }: { indicador: Indicador }) {
  const [detalle, setDetalle] = React.useState<RegistrosIndicador | null>(null);
  const [fallo, setFallo] = React.useState(false);
  async function abrir(categoria: string) {
    try { setDetalle(await registrosDeIndicador(indicador.clave, categoria)); setFallo(false); }
    catch { setDetalle(null); setFallo(true); }
  }
  return <article data-testid={`indicador-${indicador.clave}`} aria-label={indicador.titulo}
    className="rounded-md border border-[var(--ui-borde)] p-3 text-xs">
    <h4 className="font-semibold">{indicador.titulo}</h4>
    <p><strong>{indicador.valor_foco}</strong> de {indicador.denominador} (denominador) · corte {fecha(indicador.fecha_corte)}</p>
    {indicador.avance_implementacion !== null &&
      <p>Avance de implementación: {indicador.avance_implementacion} % <span className="opacity-70">({indicador.etiqueta_avance})</span></p>}
    <ul className="mt-2 flex flex-wrap gap-2">
      {Object.entries(indicador.conteos).map(([categoria, n]) => <li key={categoria}>
        <button type="button" onClick={() => abrir(categoria)} className="rounded border border-[var(--ui-borde)] px-2 py-1">
          {NOMBRES_CATEGORIA[categoria] ?? categoria}: {n}
        </button>
      </li>)}
    </ul>
    <p className="mt-2">Estados sin mapear: {indicador.sin_mapear}</p>
    <ul className="mt-1 list-disc pl-4">
      {indicador.exclusiones.map((e) => <li key={e.motivo}>Exclusión: {e.motivo}{e.cantidad !== null ? ` (${e.cantidad})` : ""}</li>)}
    </ul>
    {fallo && <p className="mt-2">No se pudieron abrir los registros de origen.</p>}
    {detalle && <section aria-label={`Registros de origen: ${indicador.titulo}`} className="mt-2">
      <p className="font-semibold">Registros de origen ({detalle.registros.length}) · {detalle.registros[0]?.origen ?? indicador.origen}</p>
      <ul className="list-disc pl-4">
        {detalle.registros.map((r) => <li key={r.id} data-testid="registro-origen">{r.descripcion} · {r.id} · {r.estado_origen ?? "sin estado"}</li>)}
      </ul>
    </section>}
  </article>;
}

export default function VistaIndicadores() {
  const [datos, setDatos] = React.useState<Indicadores | null>(null);
  React.useEffect(() => { obtenerIndicadores().then(setDatos).catch(() => setDatos(null)); }, []);
  if (!datos) return null;
  return <section aria-label="Indicadores verificables" className="flex flex-col gap-3">
    <h3 className="text-sm font-semibold">Indicadores verificables</h3>
    <p className="text-xs">Corte: {fecha(datos.fecha_corte)}. {datos.etiqueta}</p>
    {datos.indicadores.map((i) => <TarjetaIndicador key={i.clave} indicador={i} />)}
  </section>;
}
