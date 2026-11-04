"use client";
// ¤adpa ¤frontend-ide
import React from "react";
import { decidirImpacto, listarImpactos, type DecisionImpacto, type ImpactoOrganizacion } from "@/lib/biblioteca/impacto";

export default function VistaImpactos() {
  const [impactos, setImpactos] = React.useState<ImpactoOrganizacion[]>([]);
  const [error, setError] = React.useState("");
  const [motivos, setMotivos] = React.useState<Record<string, string>>({});
  const cargar = React.useCallback(() => listarImpactos().then(setImpactos).catch(() => setImpactos([])), []);
  React.useEffect(() => { cargar(); }, [cargar]);
  async function decidir(item: ImpactoOrganizacion, decision: DecisionImpacto) {
    const motivo = motivos[item.id]?.trim();
    if (!motivo) { setError("Escribe el motivo de la decisión."); return; }
    try { await decidirImpacto(item.id, decision, motivo); setError(""); await cargar(); }
    catch { setError("No se pudo registrar la decisión."); }
  }
  if (!impactos.length && !error) return null;
  return <section aria-label="Actualizaciones documentales" className="flex flex-col gap-3">
    <h3 className="text-sm font-semibold">Actualizaciones documentales</h3>
    {error && <p role="alert" className="text-xs text-red-700 dark:text-red-300">{error}</p>}
    {impactos.map((item) => <article key={item.id} data-testid="impacto-documental" className="rounded-md border border-[var(--ui-borde)] p-3 text-xs">
      <p className="font-semibold">{item.codigo} · versión {item.version}</p>
      <p>{item.documentos_afectados} documento(s) afectado(s). Estado: {item.decision}.</p>
      <label className="mt-2 flex flex-col gap-1">Motivo
        <textarea value={motivos[item.id] ?? ""} onChange={(e) => setMotivos({ ...motivos, [item.id]: e.target.value })}
          className="rounded border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-2" />
      </label>
      <div className="mt-2 flex flex-wrap gap-2">
        <button onClick={() => decidir(item, "actualizar")} type="button">Actualizar</button>
        <button onClick={() => decidir(item, "no_aplica")} type="button">No aplica</button>
        <button onClick={() => decidir(item, "pendiente")} type="button">Acción pendiente</button>
      </div>
    </article>)}
  </section>;
}
