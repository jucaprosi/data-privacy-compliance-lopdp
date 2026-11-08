"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
import React from "react";
import FormularioCargaExterna from "@/components/biblioteca/cargas/FormularioCargaExterna";
import { descargarCarga, ESTADOS_ANALISIS, listarRevisiones, type Carga } from "@/lib/biblioteca/cargas";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";

/** Revisiones del documento externo seleccionado; no aparece en documentos que no fueron subidos. */
export default function VistaCargasExternas() {
  const documentoId = useSeleccionBiblioteca((s) => s.documentoId);
  const [revisiones, setRevisiones] = React.useState<Carga[] | null>(null);
  const [mensaje, setMensaje] = React.useState("");

  const cargar = React.useCallback(async () => {
    if (!documentoId) return;
    try { setRevisiones(await listarRevisiones(documentoId)); }
    catch { setRevisiones([]); }
  }, [documentoId]);

  React.useEffect(() => { void cargar(); }, [cargar]);
  if (!documentoId || !revisiones || revisiones.length === 0) return null;

  const descargar = async (carga: Carga) => {
    try {
      const blob = await descargarCarga(carga);
      const url = URL.createObjectURL(blob);
      const enlace = document.createElement("a");
      enlace.href = url; enlace.download = carga.nombre_archivo; enlace.click();
      URL.revokeObjectURL(url);
      setMensaje("");
    } catch { setMensaje("El archivo no está disponible para descarga."); }
  };

  return (
    <section data-testid="revisiones-externas" aria-label="Revisiones del documento externo"
      className="mt-3 flex flex-col gap-2 border-t border-[var(--ui-borde)] pt-3">
      <h4 className="font-semibold">Archivo externo y sus revisiones</h4>
      <ol className="flex flex-col gap-2">
        {revisiones.map((carga) => (
          <li key={carga.id} data-testid={`revision-externa-${carga.revision_externa}`}
            className="rounded border border-[var(--ui-borde)] p-2">
            <span className="font-medium">Revisión {carga.revision_externa}</span> · versión propia {carga.version_propia}
            {" · "}
            <span data-testid="origen-maestra">
              {carga.version_maestra
                ? `Versión maestra ${carga.version_maestra.codigo} v${carga.version_maestra.version}`
                : "Origen no vinculado"}
            </span>
            {" · "}{carga.nombre_archivo}
            {" · "}<span data-testid="estado-analisis">{ESTADOS_ANALISIS[carga.estado_analisis]}</span>
            {carga.descargable && (
              <button type="button" onClick={() => void descargar(carga)} className="ml-2 underline">Descargar</button>
            )}
          </li>
        ))}
      </ol>
      {mensaje && <p role="status">{mensaje}</p>}
      <FormularioCargaExterna documentoId={documentoId} alTerminar={() => void cargar()} />
    </section>
  );
}
