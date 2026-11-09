"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Botón de descarga controlada de plantillas Word/Excel (BIB-104).
 * Se registra en la ranura `plantilla:acciones` (BIB-111) y gestiona la descarga
 * segura de versiones publicadas mediante enlaces temporales firmados.
 * SEC-19: el archivo se pide con la sesión; los 403 del token no cierran la sesión.
 */
import React from "react";
import { Download, CheckCircle2 } from "lucide-react";
import { ErrorBiblioteca } from "@/lib/biblioteca/http";
import {
  solicitarDescarga,
  descargarArchivo,
  type EnlaceDescarga,
} from "@/lib/biblioteca/descargas";
import { useSeleccionBiblioteca, type PropsVistaBiblioteca } from "@/lib/biblioteca/registro";

/** SEC-19: mensajes por código, nunca con el texto del servidor. */
const MENSAJE_TOKEN_INVALIDO = "No pudimos preparar la descarga. Inténtalo de nuevo.";
const MENSAJE_OTRA_SESION = "La descarga se pidió con otra sesión. Vuelve a pedirla desde aquí.";
const MENSAJE_GENERICO = "No se pudo descargar la plantilla. Inténtalo de nuevo.";

interface FalloDescarga { codigo: string; mensaje: string; reintentable: boolean }

export default function BotonDescargaPlantilla({ variante }: PropsVistaBiblioteca) {
  const plantillaId = useSeleccionBiblioteca((s) => s.plantillaId);
  const [descargando, setDescargando] = React.useState(false);
  const [error, setError] = React.useState<FalloDescarga | null>(null);
  const [enlace, setEnlace] = React.useState<EnlaceDescarga | null>(null);
  const enCurso = React.useRef(false);
  const botonReintentar = React.useRef<HTMLButtonElement>(null);

  React.useEffect(() => {
    setError(null);
    setEnlace(null);
  }, [plantillaId]);

  React.useEffect(() => {
    if (error?.reintentable) botonReintentar.current?.focus();
  }, [error]);

  if (!plantillaId) return null;

  /** Pide el enlace y descarga el archivo; un token inválido se reintenta en silencio una sola vez. */
  async function pedirYGuardar(id: string): Promise<EnlaceDescarga> {
    for (let intento = 0; ; intento++) {
      const res = await solicitarDescarga(id);
      try {
        await descargarArchivo(res);
        return res;
      } catch (e) {
        const reintentar = e instanceof ErrorBiblioteca && e.estado === 403
          && e.codigo === "BIB_TOKEN_DESCARGA_INVALIDO" && intento === 0;
        if (!reintentar) throw Object.assign(e as object, { delArchivo: true });
      }
    }
  }

  async function handleDescargar() {
    if (!plantillaId || enCurso.current) return;  // un doble clic no pide dos descargas
    enCurso.current = true;
    setDescargando(true);
    setError(null);
    setEnlace(null);
    try {
      setEnlace(await pedirYGuardar(plantillaId));
    } catch (e: unknown) {
      setError(falloDe(e));
    } finally {
      enCurso.current = false;
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
          aria-busy={descargando}
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
            Archivo descargado: {enlace.nombre_archivo}
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
          data-codigo={error.codigo}
          className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-red-700 dark:text-red-300"
        >
          {error.mensaje}
          {error.reintentable && (
            <button ref={botonReintentar} type="button" onClick={handleDescargar} disabled={descargando}
              className="ml-2 underline font-medium cursor-pointer">
              Reintentar descarga
            </button>
          )}
        </p>
      )}

      <p role="note" className="text-[11px] text-[var(--ui-texto-suave)]">
        La descarga del archivo maestro editable (Word/Excel) permite su adaptación local,
        sin atribuir cumplimiento legal automático.
      </p>
    </div>
  );
}

/** Mensaje del fallo; `null` en un 401, que ya atiende el manejo global de sesión caducada. */
function falloDe(e: unknown): FalloDescarga | null {
  if (!(e instanceof ErrorBiblioteca)) return { codigo: "BIB_ERROR", mensaje: MENSAJE_GENERICO, reintentable: false };
  if (e.estado === 401) return null;
  if (!(e as { delArchivo?: boolean }).delArchivo) return { codigo: e.codigo, mensaje: e.message, reintentable: false };
  if (e.codigo === "BIB_TOKEN_DESCARGA_INVALIDO") return { codigo: e.codigo, mensaje: MENSAJE_TOKEN_INVALIDO, reintentable: true };
  if (e.codigo === "BIB_TOKEN_DE_OTRA_PERSONA") return { codigo: e.codigo, mensaje: MENSAJE_OTRA_SESION, reintentable: true };
  return { codigo: e.codigo, mensaje: MENSAJE_GENERICO, reintentable: false };
}
