"use client";
// ¤adpa ¤frontend-ide
import React from "react";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";
import { aprobarRevision, devolverRevision, enviarRevision, type TipoParticipacion } from "@/lib/biblioteca/revisiones";

export default function FlujoRevision() {
  const documentoId = useSeleccionBiblioteca((s) => s.documentoId);
  const [revisionId, setRevisionId] = React.useState("");
  const [revisor, setRevisor] = React.useState("");
  const [texto, setTexto] = React.useState("");
  const [tipo, setTipo] = React.useState<TipoParticipacion>("revision");
  const [mensaje, setMensaje] = React.useState("");
  const ejecutar = async (accion: () => Promise<{ id: string; estado: string }>) => {
    setMensaje("");
    try { const resultado = await accion(); setRevisionId(resultado.id); setMensaje(`Revisión ${resultado.estado}.`); }
    catch (e) { setMensaje(e instanceof Error ? e.message : "No se pudo completar la operación."); }
  };
  if (!documentoId) return null;
  return <section aria-label="Revisión y aprobación" className="mt-3 space-y-2 border-t border-[var(--ui-borde)] pt-3 text-xs">
    <h4 className="font-semibold">Revisión y aprobación</h4>
    <p className="text-[var(--ui-texto-suave)]">La aprobación registra la autoridad y el criterio; no acredita implementación ni cierra acciones.</p>
    {!revisionId && <div className="flex flex-wrap gap-2">
      <input aria-label="Identificador del revisor" value={revisor} onChange={(e) => setRevisor(e.target.value)} className="rounded border px-2 py-1" />
      <select aria-label="Participación" value={tipo} onChange={(e) => setTipo(e.target.value as TipoParticipacion)} className="rounded border px-2 py-1">
        <option value="revision">Revisión</option><option value="asesoria">Asesoría DPD</option><option value="supervision">Supervisión DPD</option>
      </select>
      <button type="button" disabled={!revisor} onClick={() => ejecutar(() => enviarRevision(documentoId, revisor, tipo))} className="rounded border px-2 py-1">Enviar versión fija</button>
    </div>}
    {revisionId && <div className="space-y-2">
      <textarea aria-label="Motivo o criterio" value={texto} onChange={(e) => setTexto(e.target.value)} className="w-full rounded border p-2" />
      <div className="flex gap-2">
        <button type="button" disabled={texto.length < 3} onClick={() => ejecutar(() => devolverRevision(revisionId, texto))} className="rounded border px-2 py-1">Devolver con observaciones</button>
        {tipo === "revision" && <button type="button" disabled={texto.length < 3} onClick={() => ejecutar(() => aprobarRevision(revisionId, texto))} className="rounded border px-2 py-1">Aprobar con autoridad vigente</button>}
      </div>
    </div>}
    {mensaje && <p role="status">{mensaje}</p>}
  </section>;
}

