"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Botón de descarga controlada de plantillas Word/Excel (BIB-104).
 * Se registra en la ranura `plantilla:acciones` (BIB-111) y gestiona la descarga
 * segura de versiones publicadas mediante enlaces temporales firmados.
 */
import React from "react";
import { Download, CheckCircle2 } from "lucide-react";
import { ErrorBiblioteca } from "@/lib/biblioteca/http";
import {
  solicitarDescarga,
  dispararDescargaEnNavegador,
  type EnlaceDescarga,
} from "@/lib/biblioteca/descargas";
import { useSeleccionBiblioteca, type PropsVistaBiblioteca } from "@/lib/biblioteca/registro";

export default function BotonDescargaPlantilla({ variante }: PropsVistaBiblioteca) {
  const plantillaId = useSeleccionBiblioteca((s) => s.plantillaId);
  const [descargando, setDescargando] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [enlace, setEnlace] = React.useState<EnlaceDescarga | null>(null);

  React.useEffect(() => {
    setError(null);
    setEnlace(null);
  }, [plantillaId]);

  if (!plantillaId) return null;

  async function handleDescargar() {
    if (!plantillaId) return;
    setDescargando(true);
    setError(null);
    try {
      const res = await solicitarDescarga(plantillaId);
      setEnlace(res);
      dispararDescargaEnNavegador(res.url_descarga, res.nombre_archivo);
    } catch (e: unknown) {
      if (e instanceof ErrorBiblioteca) {
        setError(e.message);
      } else {
        setError("No se pudo iniciar la descarga de la plantilla.");
      }
    } finally {
      setDescargando(false);
    }
  }

  return (
    <div
      data-testid={`descarga-acciones-${variante}`}
      className="flex flex-col gap-2 pt-1"
    >
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          data-testid="boton-descargar-plantilla"
          disabled={descargando}
          onClick={handleDescargar}
          className="inline-flex items-center gap-1.5 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-3 py-1.5 font-medium cursor-pointer hover:bg-[var(--ui-boton-hover)] disabled:opacity-60"
        >
          <Download className="h-4 w-4" aria-hidden="true" />
          <span>{descargando ? "Preparando descarga…" : "Descargar archivo maestro"}</span>
        </button>
      </div>

      {enlace && (
        <div
          role="status"
          data-testid="estado-descarga-exitosa"
          className="flex flex-col gap-1 rounded-md border border-green-500/40 bg-green-500/10 p-2 text-green-700 dark:text-green-300"
        >
          <p className="flex items-center gap-1 font-medium">
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
            Descarga iniciada: {enlace.nombre_archivo}
          </p>
          <p className="text-[11px] text-[var(--ui-texto-suave)]">
            {enlace.aviso_legal}
          </p>
        </div>
      )}

      {error && (
        <p
          role="alert"
          data-testid="error-descarga"
          className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-red-700 dark:text-red-300"
        >
          {error}
        </p>
      )}

      <p role="note" className="text-[11px] text-[var(--ui-texto-suave)]">
        La descarga del archivo maestro editable (Word/Excel) permite su adaptación local,
        sin atribuir cumplimiento legal automático.
      </p>
    </div>
  );
}
