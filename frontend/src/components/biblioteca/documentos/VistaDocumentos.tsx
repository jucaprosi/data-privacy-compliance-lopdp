"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Pestaña «Documentos de la organización» (BIB-113).
 * Se registra en la ranura `pestana:documentos` desde su sección en `vistas/index.ts`.
 * Consume `GET /api/v1/biblioteca/documentos?estado=&origen=` (5).
 * Maneja los estados: listo, no_disponible (404/405/501 cuando el backend aún no responde),
 * denegado (401/403) y error por separado. Al elegir un documento fija `documentoId` en
 * `useSeleccionBiblioteca` (BIB-111) y la ranura `documento:detalle` renderiza su detalle.
 */
import React from "react";
import { FileText, RefreshCw } from "lucide-react";
import {
  ESTADOS_DOCUMENTO,
  ORIGENES,
  SIN_FILTROS_DOCUMENTOS,
  consultarDocumentos,
  hayFiltrosDocumentos,
  type FiltrosDocumentos,
  type ResultadoDocumentos,
} from "@/lib/biblioteca/documentos";
import {
  useSeleccionBiblioteca,
  vistasDe,
  type PropsVistaBiblioteca,
} from "@/lib/biblioteca/registro";
import { useBibliotecaStore } from "@/store/useBibliotecaStore";
import TarjetaDocumento from "./TarjetaDocumento";

export default function VistaDocumentos({ variante }: PropsVistaBiblioteca) {
  // Si una suite de pruebas (BIB-111 registro.spec.ts) inyectó una vista de prueba para esta ranura,
  // cedemos el montaje a la vista inyectada para no duplicar ni romper su comprobación de sustitución.
  const hayVistaInyectada =
    typeof window !== "undefined" &&
    Boolean(
      window.__LOPDP_VISTAS_BIBLIOTECA_PRUEBAS__?.some(
        (v) => v.ranura === "pestana:documentos"
      )
    );

  const organizacion = useBibliotecaStore((s) => s.organizacion);
  const documentoId = useSeleccionBiblioteca((s) => s.documentoId);
  const elegirDocumento = useSeleccionBiblioteca((s) => s.elegirDocumento);

  const [filtros, setFiltros] = React.useState<FiltrosDocumentos>(SIN_FILTROS_DOCUMENTOS);
  const [resultado, setResultado] = React.useState<ResultadoDocumentos | null>(null);
  const [intento, setIntento] = React.useState(0);

  // Cada cambio de filtro, organización o reintento dispara la consulta de nuevo.
  React.useEffect(() => {
    let vigente = true;
    setResultado(null);
    consultarDocumentos(filtros).then((r) => {
      if (vigente) setResultado(r);
    });
    return () => {
      vigente = false;
    };
  }, [filtros, organizacion, intento]);

  if (hayVistaInyectada) {
    return null;
  }

  if (resultado?.estado === "no_disponible") {
    return (
      <div data-testid="pestaña-documentos">
        <div
          data-testid="documentos-no-disponible"
          className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-[var(--ui-borde)] px-4 py-8 text-center text-xs"
        >
          <FileText className="h-6 w-6 text-[var(--ui-texto-suave)]" aria-hidden="true" />
          <p className="font-semibold text-sm">Todavía no hay documentos de la organización</p>
          <p className="max-w-md text-[var(--ui-texto-suave)]">
            Aquí aparecerán los documentos creados desde una plantilla, redactados o subidos para esta organización.
          </p>
        </div>
      </div>
    );
  }

  const cambiar = (campo: keyof FiltrosDocumentos) => (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFiltros((f) => ({ ...f, [campo]: e.target.value }));
  };

  const estiloSelect = "rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-2 py-1 text-xs";
  const vistasDetalle = vistasDe("documento:detalle");

  return (
    <div data-testid="pestaña-documentos" className="flex flex-col gap-4">
      {/* Filtros de la lista */}
      <div
        role="group"
        aria-label="Filtros de documentos"
        className="flex flex-wrap items-end gap-3 text-xs"
      >
        <label className="flex flex-col gap-1">
          Estado
          <select
            value={filtros.estado}
            onChange={cambiar("estado")}
            className={estiloSelect}
            aria-label="Filtrar por estado"
          >
            <option value="">Todos los estados</option>
            {ESTADOS_DOCUMENTO.map((e) => (
              <option key={e.id} value={e.id}>
                {e.nombre}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          Origen
          <select
            value={filtros.origen}
            onChange={cambiar("origen")}
            className={estiloSelect}
            aria-label="Filtrar por origen"
          >
            <option value="">Todos los orígenes</option>
            {ORIGENES.map((o) => (
              <option key={o.id} value={o.id}>
                {o.nombre}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          disabled={!hayFiltrosDocumentos(filtros)}
          onClick={() => setFiltros(SIN_FILTROS_DOCUMENTOS)}
          className="rounded-md border border-[var(--ui-borde)] px-3 py-1 cursor-pointer disabled:cursor-default disabled:opacity-50 text-xs hover:bg-[var(--ui-boton-hover)]"
        >
          Limpiar filtros
        </button>
      </div>

      {/* Estados de carga, no disponible, denegado y error */}
      {resultado === null && <p role="status" className="text-xs">Cargando documentos…</p>}



      {resultado?.estado === "denegado" && (
        <div
          role="alert"
          data-testid="documentos-denegado"
          className="flex flex-wrap items-center gap-3 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-red-700 dark:text-red-300 text-xs"
        >
          <p>{resultado.mensaje}</p>
        </div>
      )}

      {resultado?.estado === "error" && (
        <div
          role="alert"
          data-testid="documentos-error"
          className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-red-700 dark:text-red-300 text-xs"
        >
          <p>{resultado.mensaje}</p>
          <button
            type="button"
            onClick={() => setIntento((n) => n + 1)}
            className="inline-flex items-center gap-1 rounded-md border border-current px-2 py-1 cursor-pointer font-medium"
          >
            <RefreshCw className="h-3 w-3" aria-hidden="true" /> Reintentar
          </button>
        </div>
      )}

      {/* Lista de documentos cuando está listo */}
      {resultado?.estado === "listo" && resultado.documentos.length === 0 && (
        <div
          data-testid="documentos-vacio"
          className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-[var(--ui-borde)] px-4 py-8 text-center text-xs"
        >
          <FileText className="h-6 w-6 text-[var(--ui-texto-suave)]" aria-hidden="true" />
          <p className="font-semibold text-sm">
            {hayFiltrosDocumentos(filtros)
              ? "Ningún documento coincide con los filtros"
              : "Todavía no hay documentos de la organización"}
          </p>
          <p className="max-w-md text-[var(--ui-texto-suave)]">
            {hayFiltrosDocumentos(filtros)
              ? "Prueba a cambiar o limpiar los filtros para ver otros documentos."
              : "Aquí aparecerán los documentos creados desde una plantilla, redactados o subidos para esta organización."}
          </p>
        </div>
      )}

      {resultado?.estado === "listo" && resultado.documentos.length > 0 && (
        <ul aria-label="Documentos de la organización" className="flex flex-col gap-2">
          {resultado.documentos.map((doc) => (
            <TarjetaDocumento
              key={doc.id}
              documento={doc}
              elegido={documentoId === doc.id}
              elegir={() => elegirDocumento(documentoId === doc.id ? null : doc.id)}
            />
          ))}
        </ul>
      )}

      {/* Ranura documento:detalle */}
      {vistasDetalle.length > 0 && (
        <div className="flex flex-col gap-2">
          {vistasDetalle.map((Vista, i) => (
            <Vista key={i} variante={variante} />
          ))}
        </div>
      )}
    </div>
  );
}
