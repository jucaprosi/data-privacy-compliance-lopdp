"use client";

import { useEffect, useId, useState } from "react";
import { Download, Loader2 } from "lucide-react";

import {
  descargarInformePdf,
  mensajeErrorInforme,
  obtenerRevision,
  type EstadoRevision,
} from "@/lib/roadmap/revision";

export interface DescargarInformeProps {
  roadmapId: string;
  revision?: EstadoRevision | null;
  sincronizado?: boolean;
}

/** Descarga el informe PDF del estado de la hoja de ruta (RM-20 / RM-27). Lo genera el servidor. */
export function DescargarInforme({
  roadmapId,
  revision,
  sincronizado = false,
}: DescargarInformeProps) {
  const ayudaBloqueoId = useId();
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [revisionLocal, setRevisionLocal] = useState<EstadoRevision | null>(null);
  const [etiquetaRespuesta, setEtiquetaRespuesta] = useState(false);

  useEffect(() => {
    setError("");
    setEtiquetaRespuesta(false);
    if (sincronizado || !roadmapId) return;
    let vigente = true;
    obtenerRevision(roadmapId)
      .then((dato) => {
        if (vigente) setRevisionLocal(dato);
      })
      .catch(() => {
        if (vigente) setRevisionLocal(null);
      });
    return () => {
      vigente = false;
    };
  }, [roadmapId, sincronizado]);

  const estado = sincronizado ? (revision ?? null) : revisionLocal;
  const bloqueadoPorRevision =
    estado !== null && estado.status === "generated" && estado.generado_por !== null;
  const esHojaAnterior =
    etiquetaRespuesta ||
    (estado !== null &&
      ((estado.generado_por === null && estado.revisado_por === null) ||
        estado.etiqueta === "sin revisión registrada"));

  useEffect(() => {
    if (!bloqueadoPorRevision) {
      setError((actual) =>
        actual === "Esta hoja de ruta está pendiente de revisión. El informe se podrá descargar cuando se active."
          ? ""
          : actual,
      );
    }
  }, [estado, bloqueadoPorRevision]);

  async function descargar() {
    if (bloqueadoPorRevision || cargando) return;
    setCargando(true);
    setError("");
    try {
      const { blob, revisionHeader } = await descargarInformePdf(roadmapId);
      if (revisionHeader === "sin revisión registrada") {
        setEtiquetaRespuesta(true);
      }
      const url = URL.createObjectURL(blob);
      const enlace = document.createElement("a");
      const fecha = new Date().toISOString().slice(0, 10);
      enlace.href = url;
      enlace.download = `informe-hoja-de-ruta-${fecha}.pdf`;
      enlace.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(mensajeErrorInforme(e));
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2.5">
        <button
          type="button"
          onClick={() => void descargar()}
          disabled={cargando}
          aria-disabled={bloqueadoPorRevision ? "true" : undefined}
          aria-describedby={bloqueadoPorRevision ? ayudaBloqueoId : undefined}
          className={
            bloqueadoPorRevision
              ? "inline-flex items-center gap-2 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-2 text-xs font-semibold text-[var(--ui-texto-suave)] cursor-not-allowed"
              : "inline-flex items-center gap-2 rounded-md bg-[var(--ui-primario)] px-3 py-2 text-xs font-semibold text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#3892f3] disabled:opacity-50"
          }
        >
          {cargando ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Download className="h-4 w-4" aria-hidden="true" />
          )}
          Descargar informe (PDF)
        </button>

        {esHojaAnterior && !bloqueadoPorRevision && (
          <span className="badge-render-warning inline-flex items-center rounded px-2 py-0.5 text-[11px] font-semibold">
            Sin revisión registrada
          </span>
        )}
      </div>

      {bloqueadoPorRevision && (
        <p id={ayudaBloqueoId} className="text-xs text-[var(--ui-texto-suave)]">
          El informe se puede descargar cuando la hoja de ruta esté activa.
        </p>
      )}

      {esHojaAnterior && !bloqueadoPorRevision && (
        <p className="text-xs text-[var(--ui-texto-suave)]">
          Esta hoja de ruta es anterior a la revisión por dos personas. El informe lo indica.
        </p>
      )}

      {error && (
        <p
          role="alert"
          className="rounded-md border border-[#ff1744]/40 bg-[var(--ui-superficie)] px-3 py-2 text-xs text-zinc-100"
        >
          {error}
        </p>
      )}
    </div>
  );
}
