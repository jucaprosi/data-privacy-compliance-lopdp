"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Editor de borrador de documento (BIB-114).
 * Se monta en la ranura `documento:editor` (BIB-111).
 * Muestra el contenido Markdown editable, la lista separada de variables faltantes (`⟦falta: …⟧`),
 * los avisos aplicables de la plantilla de origen, y permite guardar mediante `PATCH` con control
 * de concurrencia optimista (`revision`).
 *
 * Reglas estrictas:
 * - Un 409 se muestra como conflicto con la opción de recargar.
 * - Nunca se anuncia «guardado» si hubo fallo de red o error 409/500.
 */
import React from "react";
import { obtenerFicha, type AvisoPlantilla } from "@/lib/biblioteca/fichas";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";
import {
  extraerVariablesFaltantes,
  guardarDocumento,
  obtenerDocumento,
  type Documento,
} from "@/lib/biblioteca/borradores";

export default function EditorBorrador() {
  const storeDocumentoId = useSeleccionBiblioteca((s) => s.documentoId);
  const docIdPruebas = typeof window !== "undefined" ? window.__LOPDP_FORMULARIOS_PRUEBAS__?.documentoId : undefined;
  const documentoId = storeDocumentoId || docIdPruebas || null;

  const [documento, setDocumento] = React.useState<Documento | null>(null);
  const [contenido, setContenido] = React.useState<string>("");
  const [cargando, setCargando] = React.useState(false);
  const [guardando, setGuardando] = React.useState(false);
  const [recargando, setRecargando] = React.useState(false);

  const [error, setError] = React.useState<string | null>(null);
  const [conflicto, setConflicto] = React.useState<string | null>(null);
  const [guardadoExitoso, setGuardadoExitoso] = React.useState(false);
  const [avisos, setAvisos] = React.useState<AvisoPlantilla[]>([]);

  // Carga inicial del documento seleccionado
  React.useEffect(() => {
    setDocumento(null);
    setContenido("");
    setError(null);
    setConflicto(null);
    setGuardadoExitoso(false);
    setAvisos([]);

    if (!documentoId) return;

    let vigente = true;
    setCargando(true);

    obtenerDocumento(documentoId)
      .then(async (res) => {
        if (!vigente) return;
        if (res.estado === "listo") {
          setDocumento(res.documento);
          setContenido(res.documento.contenido_markdown);

          // Cargar avisos de la plantilla si tiene plantilla_id
          if (res.documento.plantilla_id) {
            try {
              const ficha = await obtenerFicha(res.documento.plantilla_id);
              if (vigente && ficha.avisos && Array.isArray(ficha.avisos)) {
                setAvisos(ficha.avisos);
              }
            } catch {
              // Si falla obtener avisos, el editor sigue funcionando
            }
          }
        } else if (res.estado === "denegado") {
          setError(res.mensaje);
        } else if (res.estado === "no_disponible") {
          setError("El documento no está disponible.");
        } else {
          setError(res.mensaje || "Error al cargar el documento.");
        }
      })
      .finally(() => {
        if (vigente) setCargando(false);
      });

    return () => {
      vigente = false;
    };
  }, [documentoId]);

  if (!documentoId) return null;

  if (cargando) {
    return (
      <div data-testid="editor-cargando" className="p-4 text-xs">
        <p role="status">Cargando borrador…</p>
      </div>
    );
  }

  if (error && !documento) {
    return (
      <div data-testid="editor-error" className="p-4 text-xs">
        <p role="alert" className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-red-700 dark:text-red-300">
          {error}
        </p>
      </div>
    );
  }

  if (!documento) return null;

  // Variables faltantes calculadas del contenido en edición
  const variablesFaltantes = extraerVariablesFaltantes(contenido);

  async function handleGuardar() {
    if (!documento) return;
    setGuardando(true);
    setError(null);
    setConflicto(null);
    setGuardadoExitoso(false);

    const res = await guardarDocumento(documento.id, {
      contenido_markdown: contenido,
      revision: documento.revision,
    });

    setGuardando(false);

    if (res.estado === "listo") {
      setDocumento(res.documento);
      setContenido(res.documento.contenido_markdown);
      setGuardadoExitoso(true);
      setConflicto(null);
      setError(null);
    } else if (res.estado === "conflicto") {
      setConflicto(res.mensaje);
      setGuardadoExitoso(false);
      setError(null);
    } else if (res.estado === "denegado") {
      setError(res.mensaje);
      setGuardadoExitoso(false);
    } else if (res.estado === "no_disponible") {
      setError("El servicio de guardado no está disponible.");
      setGuardadoExitoso(false);
    } else {
      setError(res.mensaje || "Error al guardar el borrador.");
      setGuardadoExitoso(false);
    }
  }

  async function handleRecargar() {
    if (!documento) return;
    setRecargando(true);
    setError(null);
    setConflicto(null);
    setGuardadoExitoso(false);

    const res = await obtenerDocumento(documento.id);
    setRecargando(false);

    if (res.estado === "listo") {
      setDocumento(res.documento);
      setContenido(res.documento.contenido_markdown);
      setConflicto(null);
    } else {
      setError("No se pudo recargar el documento.");
    }
  }

  return (
    <article
      aria-label="Editor de borrador"
      data-testid="editor-borrador"
      className="flex flex-col gap-4 text-xs"
    >
      <header className="flex flex-col gap-1 border-b border-[var(--ui-borde)] pb-2">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="text-sm font-semibold">{documento.nombre}</h3>
          <span className="text-[var(--ui-texto-suave)]">
            Código: {documento.codigo} · Revisión: {documento.revision} · Estado: {documento.estado}
          </span>
        </div>
        {documento.editado && (
          <p className="text-[var(--ui-texto-suave)]">Este borrador tiene modificaciones guardadas.</p>
        )}
      </header>

      {/* Avisos de la plantilla */}
      {avisos.length > 0 && (
        <section aria-label="Avisos de la plantilla" data-testid="seccion-avisos" className="flex flex-col gap-1">
          {avisos.map((aviso, idx) => (
            <p
              key={idx}
              role="note"
              className={`rounded-md border px-3 py-2 ${
                aviso.nivel === "alto"
                  ? "border-red-500/40 bg-red-500/10 text-red-700 dark:text-red-300 font-medium"
                  : "border-amber-500/40 bg-amber-500/10 text-amber-800 dark:text-amber-200"
              }`}
            >
              {aviso.texto}
            </p>
          ))}
        </section>
      )}

      {/* Variables faltantes listadas aparte */}
      <section
        aria-label="Variables faltantes"
        data-testid="seccion-variables-faltantes"
        className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-3"
      >
        <h4 className="font-semibold mb-1">
          Variables faltantes ({variablesFaltantes.length})
        </h4>
        {variablesFaltantes.length > 0 ? (
          <div className="flex flex-col gap-1">
            <p className="text-amber-700 dark:text-amber-300">
              El documento muestra campos que aún no tienen valor. No podrá pasar a revisión mientras queden datos pendientes:
            </p>
            <ul data-testid="lista-variables-faltantes" className="grid gap-1 pl-4 list-disc">
              {variablesFaltantes.map((clave) => (
                <li key={clave} data-testid={`falta-${clave}`} className="font-mono text-amber-800 dark:text-amber-200">
                  ⟦falta: {clave}⟧
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="text-green-700 dark:text-green-300">
            No quedan variables faltantes en este borrador.
          </p>
        )}
      </section>

      {/* Alerta de Conflicto 409 con botón de recarga */}
      {conflicto && (
        <div
          role="alert"
          data-testid="alerta-conflicto"
          className="rounded-md border border-amber-500/40 bg-amber-500/15 p-3 flex flex-col gap-2"
        >
          <div className="flex flex-col gap-1">
            <p className="font-semibold text-amber-900 dark:text-amber-100">
              Conflicto de edición (409)
            </p>
            <p className="text-amber-800 dark:text-amber-200">{conflicto}</p>
          </div>
          <div>
            <button
              type="button"
              onClick={handleRecargar}
              disabled={recargando}
              data-testid="boton-recargar"
              className="cursor-pointer rounded-md border border-amber-600/50 bg-amber-100 dark:bg-amber-900/40 px-3 py-1 font-medium text-amber-900 dark:text-amber-100 hover:bg-amber-200"
            >
              {recargando ? "Recargando…" : "Recargar última versión"}
            </button>
          </div>
        </div>
      )}

      {/* Alerta de Error genérico / red / rechazo */}
      {error && (
        <p
          role="alert"
          data-testid="alerta-error"
          className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-red-700 dark:text-red-300"
        >
          {error}
        </p>
      )}

      {/* Mensaje de éxito al guardar */}
      {guardadoExitoso && (
        <p
          role="status"
          data-testid="mensaje-guardado"
          className="rounded-md border border-green-500/40 bg-green-500/10 px-3 py-2 text-green-700 dark:text-green-300"
        >
          Guardado correctamente (revisión {documento.revision})
        </p>
      )}

      {/* Editor Markdown */}
      <section aria-label="Editor de contenido" className="flex flex-col gap-1">
        <label htmlFor="editor-contenido-markdown" className="font-medium">
          Contenido Markdown
        </label>
        <textarea
          id="editor-contenido-markdown"
          data-testid="editor-markdown"
          rows={16}
          value={contenido}
          onChange={(e) => {
            setContenido(e.target.value);
            setGuardadoExitoso(false);
          }}
          className="w-full font-mono text-xs rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-3 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </section>

      {/* Barra de acciones */}
      <div className="flex items-center gap-2 pt-1">
        <button
          type="button"
          onClick={handleGuardar}
          disabled={guardando || recargando}
          data-testid="boton-guardar"
          className="cursor-pointer rounded-md bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 font-medium disabled:opacity-60"
        >
          {guardando ? "Guardando…" : "Guardar borrador"}
        </button>
      </div>
    </article>
  );
}
