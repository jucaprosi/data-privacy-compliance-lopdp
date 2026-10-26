"use client";

import { useState } from "react";
import { Download, Loader2 } from "lucide-react";

import { roadmapApi } from "@/lib/roadmap/cliente";

/** Descarga el informe PDF del estado de la hoja de ruta (RM-20). Lo genera el servidor. */
export function DescargarInforme({ roadmapId }: { roadmapId: string }) {
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  async function descargar() {
    setCargando(true);
    setError("");
    try {
      const blob = await roadmapApi.descargarInforme(roadmapId);
      const url = URL.createObjectURL(blob);
      const enlace = document.createElement("a");
      enlace.href = url;
      enlace.download = `informe-${roadmapId}.pdf`;
      enlace.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo descargar el informe.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={descargar}
        disabled={cargando}
        className="inline-flex items-center gap-2 rounded-md bg-[var(--ui-primario)] px-3 py-2 text-xs font-semibold text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] disabled:opacity-50"
      >
        {cargando ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Download className="h-4 w-4" aria-hidden="true" />}
        Descargar informe (PDF)
      </button>
      {error && (
        <p role="alert" className="mt-2 text-xs">
          {error}
        </p>
      )}
    </div>
  );
}
