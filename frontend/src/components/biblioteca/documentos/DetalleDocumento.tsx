"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Vista de detalle de un documento de la organización (BIB-113).
 * Se registra en la ranura `documento:detalle` desde `vistas/index.ts`.
 * Consume `GET /api/v1/biblioteca/documentos/{id}` (6).
 * Al recibir 404 (documento ajeno o no existente), lo expone claramente como no encontrado.
 * No edita (BIB-114) ni cambia el estado (BIB-301); monta sus ranuras correspondientes.
 */
import React from "react";
import { RefreshCw, X } from "lucide-react";
import {
  ETIQUETAS_ESTADO,
  ETIQUETAS_ORIGEN,
  obtenerDocumento,
  type Documento,
  type ResultadoDocumento,
} from "@/lib/biblioteca/documentos";
import {
  useSeleccionBiblioteca,
  vistasDe,
  type PropsVistaBiblioteca,
} from "@/lib/biblioteca/registro";
import { useBibliotecaStore } from "@/store/useBibliotecaStore";

export default function DetalleDocumento({ variante }: PropsVistaBiblioteca) {
  const documentoId = useSeleccionBiblioteca((s) => s.documentoId);
  const elegirDocumento = useSeleccionBiblioteca((s) => s.elegirDocumento);
  const organizacion = useBibliotecaStore((s) => s.organizacion);

  const [resultado, setResultado] = React.useState<ResultadoDocumento | null>(null);
  const [intento, setIntento] = React.useState(0);

  React.useEffect(() => {
    setResultado(null);
    if (!documentoId) return;

    let vigente = true;
    obtenerDocumento(documentoId).then((r) => {
      if (vigente) setResultado(r);
    });

    return () => {
      vigente = false;
    };
  }, [documentoId, organizacion, intento]);

  if (!documentoId) return null;

  const cerrar = () => elegirDocumento(null);

  if (resultado === null) {
    return (
      <div data-testid="detalle-cargando" className="rounded-lg border border-[var(--ui-borde)] p-4 text-xs">
        <p role="status">Cargando documento…</p>
      </div>
    );
  }

  if (resultado.estado === "no_encontrado") {
    return (
      <div
        role="alert"
        data-testid="documento-no-encontrado"
        className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-amber-800 dark:text-amber-200 text-xs"
      >
        <p>{resultado.mensaje}</p>
        <button
          type="button"
          onClick={cerrar}
          className="inline-flex items-center gap-1 rounded-md border border-current px-2 py-1 cursor-pointer font-medium hover:bg-amber-500/20"
        >
          <X className="h-3 w-3" aria-hidden="true" /> Cerrar
        </button>
      </div>
    );
  }

  if (resultado.estado === "no_disponible") {
    return (
      <div
        role="alert"
        data-testid="documento-detalle-no-disponible"
        className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-3 py-2 text-xs"
      >
        <p>El servicio de consulta de documentos no está disponible en este momento.</p>
        <button
          type="button"
          onClick={cerrar}
          className="rounded-md border border-[var(--ui-borde)] px-2 py-1 cursor-pointer hover:bg-[var(--ui-boton-hover)]"
        >
          Cerrar
        </button>
      </div>
    );
  }

  if (resultado.estado === "denegado") {
    return (
      <div
        role="alert"
        data-testid="documento-detalle-denegado"
        className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-red-700 dark:text-red-300 text-xs"
      >
        <p>{resultado.mensaje}</p>
        <button
          type="button"
          onClick={cerrar}
          className="inline-flex items-center gap-1 rounded-md border border-current px-2 py-1 cursor-pointer"
        >
          <X className="h-3 w-3" aria-hidden="true" /> Cerrar
        </button>
      </div>
    );
  }

  if (resultado.estado === "error") {
    return (
      <div
        role="alert"
        data-testid="documento-detalle-error"
        className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-red-700 dark:text-red-300 text-xs"
      >
        <p>{resultado.mensaje}</p>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIntento((n) => n + 1)}
            className="inline-flex items-center gap-1 rounded-md border border-current px-2 py-1 cursor-pointer"
          >
            <RefreshCw className="h-3 w-3" aria-hidden="true" /> Reintentar
          </button>
          <button
            type="button"
            onClick={cerrar}
            className="rounded-md border border-current px-2 py-1 cursor-pointer"
          >
            Cerrar
          </button>
        </div>
      </div>
    );
  }

  const doc: Documento = resultado.documento;
  const etiquetaOrigen = ETIQUETAS_ORIGEN[doc.origen] ?? doc.origen;
  const etiquetaEstado = ETIQUETAS_ESTADO[doc.estado] ?? doc.estado;
  const vistasAcciones = vistasDe("documento:acciones");
  const vistasEditor = vistasDe("documento:editor");

  return (
    <article
      aria-label="Detalle del documento"
      data-testid="detalle-documento"
      className="flex flex-col gap-3 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-fondo)] p-4 text-xs"
    >
      <header className="flex flex-wrap items-start justify-between gap-2 border-b border-[var(--ui-borde)] pb-3">
        <div className="flex flex-col gap-1">
          <h3 className="text-base font-semibold">{doc.nombre}</h3>
          <p className="text-[var(--ui-texto-suave)]">
            {doc.codigo} ·{" "}
            <span data-testid="detalle-etiqueta-origen" className="font-medium text-[var(--ui-texto)]">
              {etiquetaOrigen}
            </span>{" "}
            ·{" "}
            <span data-testid="detalle-etiqueta-estado" className="font-medium text-[var(--ui-texto)]">
              {etiquetaEstado}
            </span>
            {doc.plantilla_version ? ` · plantilla versión ${doc.plantilla_version}` : ""}
            {` · revisión ${doc.revision}`}
            {doc.editado ? " · (editado)" : ""}
          </p>
        </div>
        <button
          type="button"
          aria-label="Cerrar detalle"
          onClick={cerrar}
          className="inline-flex items-center gap-1 rounded-md border border-[var(--ui-borde)] px-2.5 py-1 text-xs cursor-pointer hover:bg-[var(--ui-boton-hover)]"
        >
          <X className="h-3.5 w-3.5" aria-hidden="true" /> Cerrar
        </button>
      </header>

      <dl className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        <div>
          <dt className="font-medium text-[var(--ui-texto-suave)]">Origen</dt>
          <dd>{etiquetaOrigen}</dd>
        </div>
        <div>
          <dt className="font-medium text-[var(--ui-texto-suave)]">Estado</dt>
          <dd>{etiquetaEstado}</dd>
        </div>
        <div>
          <dt className="font-medium text-[var(--ui-texto-suave)]">Fecha de emisión</dt>
          <dd>{doc.fecha_emision ?? "—"}</dd>
        </div>
        <div>
          <dt className="font-medium text-[var(--ui-texto-suave)]">Próxima revisión</dt>
          <dd>{doc.proxima_revision}</dd>
        </div>
        <div>
          <dt className="font-medium text-[var(--ui-texto-suave)]">Revisión actual</dt>
          <dd>{doc.revision} {doc.editado ? "(con cambios respecto a la plantilla)" : ""}</dd>
        </div>
        <div>
          <dt className="font-medium text-[var(--ui-texto-suave)]">Huella de integridad (SHA-256)</dt>
          <dd>
            <code className="font-mono text-[11px] break-all">{doc.sha256}</code>
          </dd>
        </div>
        {doc.aprobado_por && (
          <div className="sm:col-span-2">
            <dt className="font-medium text-[var(--ui-texto-suave)]">Aprobación</dt>
            <dd>
              Aprobado por {doc.aprobado_por}
              {doc.aprobado_en ? ` el ${doc.aprobado_en}` : ""}
            </dd>
          </div>
        )}
      </dl>

      {doc.variables_faltantes && doc.variables_faltantes.length > 0 ? (
        <div
          data-testid="variables-faltantes"
          className="rounded-md border border-amber-500/40 bg-amber-500/10 p-3"
        >
          <p className="font-semibold text-amber-800 dark:text-amber-200">
            Variables faltantes ({doc.variables_faltantes.length})
          </p>
          <p className="mt-0.5 text-[var(--ui-texto-suave)] text-[11px]">
            El documento no puede pasar a revisión mientras tenga variables sin completar.
          </p>
          <ul className="mt-2 list-disc list-inside space-y-0.5">
            {doc.variables_faltantes.map((v) => (
              <li key={v}>
                <code className="font-mono text-xs">{v}</code>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div data-testid="variables-faltantes-vacio" className="rounded-md border border-green-500/30 bg-green-500/10 p-2.5">
          <p className="text-green-700 dark:text-green-300 font-medium">
            Sin variables faltantes: todos los campos requeridos están completos.
          </p>
        </div>
      )}

      <div
        data-testid="documento-contenido"
        className="flex flex-col gap-1.5 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-3"
      >
        <h4 className="font-semibold text-xs">Contenido</h4>
        <pre className="whitespace-pre-wrap font-mono text-xs overflow-x-auto max-h-96">
          {doc.contenido_markdown}
        </pre>
      </div>

      {vistasAcciones.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-2 border-t border-[var(--ui-borde)]">
          {vistasAcciones.map((Vista, i) => (
            <Vista key={i} variante={variante} />
          ))}
        </div>
      )}

      {vistasEditor.length > 0 && (
        <div className="mt-2">
          {vistasEditor.map((Vista, i) => (
            <Vista key={i} variante={variante} />
          ))}
        </div>
      )}
    </article>
  );
}
