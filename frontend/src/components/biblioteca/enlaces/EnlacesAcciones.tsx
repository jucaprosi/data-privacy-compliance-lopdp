"use client";

// ¤adpa ¤rbac-tenant
import React from "react";
import { crearEnlace, eliminarEnlace, listarEnlaces, type EnlaceDocumento } from "@/lib/biblioteca/enlaces";
import { obtenerDocumento } from "@/lib/biblioteca/documentos";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";

export default function EnlacesAcciones() {
  const documentoId = useSeleccionBiblioteca((s) => s.documentoId);
  const [enlaces, setEnlaces] = React.useState<EnlaceDocumento[]>([]);
  const [revision, setRevision] = React.useState(1);
  const [accionId, setAccionId] = React.useState("");
  const [mensaje, setMensaje] = React.useState("");

  const recargar = React.useCallback(async () => {
    if (!documentoId) return;
    try {
      const [lista, documento] = await Promise.all([listarEnlaces(documentoId), obtenerDocumento(documentoId)]);
      setEnlaces(lista);
      if (documento.estado === "listo") setRevision(documento.documento.revision);
      setMensaje("");
    } catch (error) {
      setMensaje(error instanceof Error ? error.message : "No se pudieron consultar los enlaces.");
    }
  }, [documentoId]);

  React.useEffect(() => { void recargar(); }, [recargar]);
  if (!documentoId) return null;

  const enlazar = async () => {
    if (!accionId.trim()) return;
    try {
      await crearEnlace(documentoId, accionId.trim(), revision);
      setAccionId("");
      await recargar();
    } catch (error) {
      setMensaje(error instanceof Error ? error.message : "No se pudo crear el enlace.");
    }
  };

  return (
    <section aria-label="Acciones vinculadas" className="mt-2 rounded-md border border-[var(--ui-borde)] p-3">
      <h4 className="font-semibold">Acciones y brechas vinculadas</h4>
      <p className="text-[11px] text-[var(--ui-texto-suave)]">
        Los enlaces conservan la revisión concreta. Enlazar o retirar no cambia el estado de la acción.
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        <input aria-label="ID de acción" value={accionId} onChange={(e) => setAccionId(e.target.value)}
          className="min-w-56 rounded border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-2 py-1"
          placeholder="ID de acción canónica" />
        <button type="button" onClick={() => void enlazar()}
          className="rounded border border-[var(--ui-borde)] px-2 py-1 font-medium">Enlazar revisión {revision}</button>
      </div>
      {mensaje && <p role="alert" className="mt-2 text-red-600">{mensaje}</p>}
      <ul className="mt-3 space-y-2" data-testid="enlaces-acciones">
        {enlaces.map((enlace) => (
          <li key={enlace.id} className="rounded border border-[var(--ui-borde)] p-2">
            <div className="flex justify-between gap-2">
              <p><strong>{enlace.accion_titulo}</strong> · {enlace.accion_estado}</p>
              <button type="button" aria-label={`Retirar enlace ${enlace.accion_titulo}`}
                onClick={() => void eliminarEnlace(documentoId, enlace.id).then(recargar).catch((e) => setMensaje(e.message))}
                className="text-red-600">Retirar</button>
            </div>
            <p>Revisión {enlace.documento_revision} · requisito {enlace.requisito}</p>
            {enlace.hallazgo_id ? <p>Hallazgo: {enlace.hallazgo_titulo} ({enlace.hallazgo_id})</p> : <p>Sin hallazgo de origen</p>}
            {enlace.pregunta && <p>Pregunta {enlace.pregunta} · assessment versión {enlace.assessment_version ?? "no disponible"}</p>}
          </li>
        ))}
      </ul>
    </section>
  );
}
