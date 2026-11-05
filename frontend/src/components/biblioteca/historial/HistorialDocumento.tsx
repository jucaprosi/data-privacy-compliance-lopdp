"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
import React from "react";
import { obtenerConservacion, obtenerCronologia, restaurarRevision, type ConservacionDocumento,
  type EventoCronologia, type TipoEvento } from "@/lib/biblioteca/historial";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";

const etiquetas: Record<TipoEvento, string> = {
  cambio: "Cambio", descarga: "Descarga", generacion: "Generación", aprobacion: "Aprobación",
  notificacion: "Notificación", reapertura: "Reapertura", restauracion: "Restauración",
};

export default function HistorialDocumento() {
  const documentoId = useSeleccionBiblioteca((s) => s.documentoId);
  const [eventos, setEventos] = React.useState<EventoCronologia[] | null>(null);
  const [conservacion, setConservacion] = React.useState<ConservacionDocumento | null>(null);
  const [mensaje, setMensaje] = React.useState("");

  const cargar = React.useCallback(async () => {
    if (!documentoId) return;
    try {
      const [historial, politica] = await Promise.all([
        obtenerCronologia(documentoId), obtenerConservacion(documentoId),
      ]);
      setEventos(historial); setConservacion(politica); setMensaje("");
    } catch { setMensaje("No se pudo cargar el historial autorizado."); }
  }, [documentoId]);

  React.useEffect(() => { void cargar(); }, [cargar]);
  if (!documentoId) return null;

  const restaurar = async (evento: EventoCronologia) => {
    if (!evento.revision) return;
    try {
      await restaurarRevision(documentoId, evento.revision, "Restauración solicitada desde la cronología");
      setMensaje(`La revisión ${evento.revision} se restauró como una revisión nueva.`);
      await cargar();
    } catch { setMensaje("No se pudo restaurar la revisión."); }
  };

  return (
    <section data-testid="historial-documento" className="mt-3 flex flex-col gap-3 border-t border-[var(--ui-borde)] pt-3">
      <h4 className="font-semibold">Cronología y conservación</h4>
      {conservacion?.bloqueo_legal && <p role="status" data-testid="bloqueo-legal" className="text-amber-700">Bloqueo legal activo: no se permite eliminar.</p>}
      {!conservacion?.politica_aprobada && <p data-testid="politica-pendiente" className="text-[var(--ui-texto-suave)]">Política de conservación pendiente de aprobación; no se ejecutará borrado.</p>}
      {mensaje && <p role="status">{mensaje}</p>}
      {eventos === null ? <p>Cargando cronología…</p> : (
        <ol className="flex flex-col gap-2">
          {eventos.map((evento) => (
            <li key={evento.id} data-testid={`evento-${evento.tipo}`} className="rounded border border-[var(--ui-borde)] p-2">
              <span className="font-medium">{etiquetas[evento.tipo]}</span>
              {evento.revision ? ` · revisión ${evento.revision}` : ""} · {new Date(evento.creado_en).toLocaleString()}
              {evento.tipo === "cambio" && evento.revision && <button type="button" onClick={() => void restaurar(evento)} className="ml-2 underline">Restaurar como nueva revisión</button>}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
