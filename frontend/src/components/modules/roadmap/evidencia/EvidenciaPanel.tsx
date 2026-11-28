// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

import React, { useCallback, useEffect, useId, useMemo, useState } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";
import { AlertCircle, CheckCircle2, CircleDashed, Loader2, Lock, UploadCloud, XCircle } from "lucide-react";

import { formatearTamano } from "@/lib/evidencias/hash";
import { roadmapApi, type EvidenciaConDobleValidacion } from "@/lib/roadmap/cliente";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import { ApiError } from "@/types/roadmap";
import type { EvidenceValidationStatus } from "@/types/roadmap";
type TaskEvidence = EvidenciaConDobleValidacion;
import {
  EXTENSIONES_PERMITIDAS,
  TAMANO_MAXIMO_BYTES,
  TIPOS_PERMITIDOS,
  bloqueaCuatroOjos,
  evidenciaVisible,
  nombreDeArchivo,
  puedeSubir,
  puedeValidar,
} from "./reglas";
import { MENSAJE_PASO, subirEvidencia, type PasoSubida } from "./subirEvidencia";

export interface EvidenciaPanelProps {
  taskId: string;
  titulo?: string;
}

interface ErrorVisible {
  mensaje: string;
  codigo?: string;
  accion?: string | null;
}

interface Revision {
  decision: Exclude<EvidenceValidationStatus, "pending"> | null;
  comentario: string;
  ocupada: boolean;
  aviso: string | null;
  error: ErrorVisible | null;
}

// === RM-25c ===
const ETIQUETA_ROL: Record<string, string> = {
  coordinador: "Coordinador",
  dpo: "DPO",
  implementador: "Implementador",
  admin_organizacion: "Administrador de la organización",
  responsable_area: "Responsable de área",
  auditor: "Auditor",
};

/** Mensajes fijos por código: el texto del servidor no se muestra (revisión UX/UI). */
function mensajeDePrimeraValidacion(codigo: string | undefined): string {
  switch (codigo) {
    case "SOD_VIOLATION":
      return "No puedes hacer la primera validación de una evidencia que subiste tú. Debe hacerla otra persona.";
    case "RM_PRIMERA_VALIDACION_YA_REGISTRADA":
      return "Esta evidencia ya tiene su primera validación. Actualiza la lista para verla.";
    case "RM_EVIDENCIA_NO_PENDIENTE":
      return "Esta evidencia ya fue resuelta y no admite primera validación.";
    default:
      return "No se pudo registrar la primera validación. Inténtalo de nuevo.";
  }
}

function fechaDeValidacion(iso: string | null | undefined): string {
  const fecha = iso ? new Date(iso) : null;
  return fecha && !Number.isNaN(fecha.getTime()) ? ` · ${fecha.toLocaleDateString("es-EC")}` : "";
}

function lineaDeHistorial(quien: string, rol: string | null | undefined, paso: string, iso: string | null | undefined): string {
  const etiqueta = rol ? (ETIQUETA_ROL[rol] ?? rol) : null;
  return `${[quien, etiqueta, paso].filter(Boolean).join(" · ")}${fechaDeValidacion(iso)}`;
}
// === fin RM-25c ===

const REVISION_INICIAL: Revision = { decision: null, comentario: "", ocupada: false, aviso: null, error: null };

const ESTADO_VALIDACION: Record<EvidenceValidationStatus, { texto: string; clase: string; icono: React.ReactNode }> = {
  pending: {
    texto: "Pendiente de validación",
    clase: "badge-render-warning",
    icono: <CircleDashed className="w-3.5 h-3.5" aria-hidden="true" />,
  },
  approved: {
    texto: "Aprobada",
    clase: "badge-render-success",
    icono: <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />,
  },
  rejected: {
    texto: "Rechazada",
    clase: "badge-render-danger",
    icono: <XCircle className="w-3.5 h-3.5" aria-hidden="true" />,
  },
};

const BOTON =
  "inline-flex items-center gap-1.5 rounded-md border border-[var(--ui-borde-control)] bg-[var(--ui-boton)] px-2.5 py-1.5 text-xs " +
  "font-semibold text-[var(--foreground)] hover:bg-[var(--ui-boton-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ui-enlace)] " +
  "disabled:opacity-50 disabled:cursor-not-allowed";

function aErrorVisible(err: unknown): ErrorVisible {
  if (err instanceof ApiError) return { mensaje: err.message, codigo: err.code, accion: err.action_required };
  if (err instanceof Error) return { mensaje: err.message };
  return { mensaje: "No se pudo completar la operación. Inténtalo de nuevo." };
}

function mensajeDeRechazo(rechazo: FileRejection): string {
  const codigos = rechazo.errors.map((e) => e.code);
  if (codigos.includes("file-invalid-type")) {
    return `«${rechazo.file.name}»: tipo de archivo no permitido. Extensiones admitidas: ${EXTENSIONES_PERMITIDAS.join(", ")}.`;
  }
  if (codigos.includes("file-too-large")) {
    return `«${rechazo.file.name}»: supera el tamaño máximo de ${formatearTamano(TAMANO_MAXIMO_BYTES)}.`;
  }
  return `«${rechazo.file.name}»: el archivo no se puede subir.`;
}

function BloqueError({ error, testId }: { error: ErrorVisible; testId?: string }) {
  return (
    <div role="alert" data-testid={testId} className="flex items-start gap-2 p-2.5 rounded-md bg-[var(--ui-error-fondo)] border border-[var(--ui-error-borde)] text-xs">
      <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[var(--ui-error-texto)]" aria-hidden="true" />
      <div className="space-y-0.5">
        <p>{error.mensaje}</p>
        {error.codigo && <p className="text-[var(--ui-texto-suave)]">Código: {error.codigo}</p>}
        {error.accion && <p className="text-[var(--ui-texto-suave)]">Acción requerida: {error.accion}</p>}
      </div>
    </div>
  );
}

export function EvidenciaPanel({ taskId, titulo }: EvidenciaPanelProps) {
  const idBase = useId();
  const rol = useRoadmapStore((s) => s.session.role);
  const usuarioId = useRoadmapStore((s) => s.session.userId);

  const [evidencias, setEvidencias] = useState<TaskEvidence[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorLista, setErrorLista] = useState<ErrorVisible | null>(null);
  const [paso, setPaso] = useState<PasoSubida | null>(null);
  const [errorSubida, setErrorSubida] = useState<ErrorVisible | null>(null);
  const [ultimoArchivo, setUltimoArchivo] = useState<File | null>(null);
  const [rechazos, setRechazos] = useState<string[]>([]);
  const [revisiones, setRevisiones] = useState<Record<string, Revision>>({});
  // === RM-25c ===
  const [primeras, setPrimeras] = useState<Record<string, { ocupada: boolean; error: string | null }>>({});
  // === fin RM-25c ===

  const subiendo = paso !== null;
  const puedeSubirRol = puedeSubir(rol);
  const puedeValidarRol = puedeValidar(rol);

  const cargar = useCallback(async () => {
    setCargando(true);
    setErrorLista(null);
    try {
      setEvidencias(await roadmapApi.listEvidence(taskId));
    } catch (err: unknown) {
      setErrorLista(aErrorVisible(err));
    } finally {
      setCargando(false);
    }
  }, [taskId]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const iniciarSubida = useCallback(
    async (archivo: File) => {
      setUltimoArchivo(archivo);
      setErrorSubida(null);
      setRechazos([]);
      try {
        const registrada = await subirEvidencia(taskId, archivo, setPaso);
        setEvidencias((previo) => [...previo, registrada]);
        setUltimoArchivo(null);
      } catch (err: unknown) {
        setErrorSubida(aErrorVisible(err));
      } finally {
        setPaso(null);
      }
    },
    [taskId],
  );

  const accept = useMemo(
    () => Object.fromEntries(Object.entries(TIPOS_PERMITIDOS).map(([mime, ext]) => [mime, [...ext]])),
    [],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept,
    maxSize: TAMANO_MAXIMO_BYTES,
    multiple: false,
    disabled: !puedeSubirRol || subiendo,
    onDropAccepted: (archivos) => void iniciarSubida(archivos[0]),
    onDropRejected: (rechazados) => setRechazos(rechazados.map(mensajeDeRechazo)),
  });

  function actualizarRevision(id: string, cambios: Partial<Revision>) {
    setRevisiones((previo) => ({ ...previo, [id]: { ...(previo[id] ?? REVISION_INICIAL), ...cambios } }));
  }

  async function confirmarRevision(evidencia: TaskEvidence) {
    const revision = revisiones[evidencia.id] ?? REVISION_INICIAL;
    if (!revision.decision) return;
    if (revision.decision === "rejected" && revision.comentario.trim() === "") {
      actualizarRevision(evidencia.id, { aviso: "Para rechazar una evidencia indica el motivo en el comentario." });
      return;
    }
    actualizarRevision(evidencia.id, { ocupada: true, aviso: null, error: null });
    try {
      const actualizada = await roadmapApi.validateEvidence(taskId, evidencia.id, {
        validation_status: revision.decision,
        notes: revision.comentario.trim(),
      });
      setEvidencias((previo) => previo.map((e) => (e.id === evidencia.id ? actualizada : e)));
      setRevisiones((previo) => ({ ...previo, [evidencia.id]: REVISION_INICIAL }));
    } catch (err: unknown) {
      actualizarRevision(evidencia.id, { ocupada: false, error: aErrorVisible(err) });
    }
  }

  // === RM-25c ===
  async function registrarPrimera(evidencia: TaskEvidence) {
    if (primeras[evidencia.id]?.ocupada) return;
    setPrimeras((previo) => ({ ...previo, [evidencia.id]: { ocupada: true, error: null } }));
    try {
      const actualizada = await roadmapApi.registrarPrimeraValidacion(taskId, evidencia.id);
      setEvidencias((previo) => previo.map((e) => (e.id === evidencia.id ? actualizada : e)));
      setPrimeras((previo) => ({ ...previo, [evidencia.id]: { ocupada: false, error: null } }));
    } catch (err: unknown) {
      const codigo = err instanceof ApiError ? err.code : undefined;
      setPrimeras((previo) => ({
        ...previo,
        [evidencia.id]: { ocupada: false, error: mensajeDePrimeraValidacion(codigo) },
      }));
    }
  }
  // === fin RM-25c ===

  const visibles = evidencias.filter((e) => evidenciaVisible(rol, usuarioId, e));

  return (
    <section aria-label="Evidencia de la tarea" className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-5 space-y-4 text-[var(--foreground)]">
      <header>
        <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--foreground)]">Evidencia</h2>
        {titulo && <p className="text-[11px] text-[var(--ui-texto-suave)] mt-0.5">{titulo}</p>}
      </header>

      {puedeSubirRol ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition flex flex-col items-center gap-2 ${
            isDragActive ? "border-[var(--ui-info-borde)] bg-[var(--ui-info-fondo)]" : "border-[var(--ui-borde)] hover:border-[var(--ui-primario)]"
          } ${subiendo ? "opacity-60 cursor-not-allowed" : ""}`}
        >
          <input {...getInputProps({ "aria-label": "Archivo de evidencia" })} />
          <UploadCloud className="w-5 h-5 text-[var(--ui-enlace)]" aria-hidden="true" />
          <p className="text-xs font-semibold text-[var(--foreground)]">Suelta aquí el archivo o haz clic para elegirlo</p>
          <p className="text-[11px] text-[var(--ui-texto-suave)]">
            Se admiten {EXTENSIONES_PERMITIDAS.join(", ")} de hasta {formatearTamano(TAMANO_MAXIMO_BYTES)}.
          </p>
        </div>
      ) : (
        <div role="note" className="flex items-start gap-2.5 p-3 rounded-lg bg-[var(--ui-aviso-fondo)] border border-[var(--ui-aviso-borde)] text-xs">
          <Lock className="w-4 h-4 shrink-0 mt-0.5 text-[var(--ui-aviso-texto)]" aria-hidden="true" />
          <p>
            Tu rol actual es <strong>{rol}</strong> y no sube evidencia. Solo la suben el responsable de área y el
            coordinador.
          </p>
        </div>
      )}

      {rechazos.length > 0 && (
        <ul role="alert" data-testid="rechazos" className="space-y-1 text-xs text-[var(--ui-error-texto)]">
          {rechazos.map((mensaje) => (
            <li key={mensaje}>{mensaje}</li>
          ))}
        </ul>
      )}

      {subiendo && paso && (
        <div role="status" aria-live="polite" className="flex items-center gap-2.5 p-3 rounded-lg bg-[var(--ui-info-fondo)] border border-[var(--ui-info-borde)] text-xs">
          <Loader2 className="w-4 h-4 animate-spin text-[var(--ui-enlace)]" aria-hidden="true" />
          <p data-testid="subida-progreso">{MENSAJE_PASO[paso]}</p>
        </div>
      )}

      {errorSubida && (
        <div className="space-y-2">
          <BloqueError error={errorSubida} testId="error-subida" />
          {ultimoArchivo && (
            <button type="button" className={BOTON} onClick={() => void iniciarSubida(ultimoArchivo)} disabled={subiendo}>
              Reintentar la subida de {ultimoArchivo.name}
            </button>
          )}
        </div>
      )}

      {rol === "responsable_area" && (
        <p className="text-[11px] text-[var(--ui-texto-suave)]">Como responsable de área, aquí solo ves la evidencia que subiste tú.</p>
      )}

      {cargando && (
        <p role="status" className="flex items-center gap-2 text-xs text-[var(--ui-texto-suave)]">
          <Loader2 className="w-4 h-4 animate-spin text-[var(--ui-enlace)]" aria-hidden="true" />
          Cargando la evidencia…
        </p>
      )}

      {errorLista && (
        <div className="space-y-2">
          <BloqueError error={errorLista} testId="error-lista" />
          <button type="button" className={BOTON} onClick={() => void cargar()}>
            Reintentar la carga
          </button>
        </div>
      )}

      {!cargando && !errorLista && visibles.length === 0 && (
        <p role="status" data-testid="sin-evidencia" className="text-xs text-[var(--ui-texto-suave)]">
          Esta tarea todavía no tiene evidencia registrada.
        </p>
      )}

      <ul aria-label="Evidencias registradas" className="space-y-3">
        {visibles.map((evidencia) => {
          const revision = revisiones[evidencia.id] ?? REVISION_INICIAL;
          const estado = ESTADO_VALIDACION[evidencia.validation_status];
          const bloqueada = bloqueaCuatroOjos(usuarioId, evidencia);
          const pendiente = evidencia.validation_status === "pending";
          const id = (campo: string) => `${idBase}-${evidencia.id}-${campo}`;
          return (
            <li
              key={evidencia.id}
              data-testid={`evidencia-${evidencia.id}`}
              className="rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] p-4 space-y-2.5"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-[var(--foreground)] break-all">{nombreDeArchivo(evidencia.clave_objeto)}</p>
                  <p className="text-[11px] text-[var(--ui-texto-suave)] mt-0.5">
                    {evidencia.file_size != null ? `${formatearTamano(evidencia.file_size)} · ` : ""}
                    Subida por {evidencia.uploaded_by ?? "desconocido"}
                    {evidencia.file_hash ? ` · huella ${evidencia.file_hash.slice(0, 12)}…` : ""}
                  </p>
                </div>
                <span
                  data-testid={`validacion-${evidencia.id}`}
                  className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold ${estado.clase}`}
                >
                  {estado.icono}
                  {estado.texto}
                </span>
              </div>

              {evidencia.notes && (
                <p className="text-xs text-[var(--ui-texto-suave)]">
                  <span className="text-[var(--ui-texto-suave)]">Comentario:</span> {evidencia.notes}
                </p>
              )}

              {/* === RM-25c === */}
              {evidencia.requiere_revalidacion && (
                <p role="status" data-testid={`pendiente-final-${evidencia.id}`} className="text-[11px] font-semibold text-[var(--ui-aviso-texto)]">
                  Pendiente de validación final
                </p>
              )}
              {(evidencia.primera_validacion_por || (evidencia.validated_by && evidencia.validation_status !== "pending")) && (
                <ul aria-label="Historial de validación" data-testid={`historial-${evidencia.id}`} className="space-y-0.5 text-[11px] text-[var(--ui-texto-suave)]">
                  {evidencia.primera_validacion_por && (
                    <li>
                      {lineaDeHistorial(evidencia.primera_validacion_por, evidencia.primera_validacion_rol, "Primera validación", evidencia.primera_validacion_en)}
                    </li>
                  )}
                  {evidencia.validated_by && evidencia.validation_status !== "pending" && (
                    <li>{lineaDeHistorial(evidencia.validated_by, evidencia.validado_rol, "Validación final", evidencia.validated_at)}</li>
                  )}
                </ul>
              )}
              {rol === "coordinador" && pendiente && !evidencia.primera_validacion_por && (
                <div className="space-y-1.5">
                  <button
                    type="button"
                    className={BOTON}
                    disabled={bloqueada || primeras[evidencia.id]?.ocupada === true}
                    onClick={() => void registrarPrimera(evidencia)}
                  >
                    {primeras[evidencia.id]?.ocupada ? "Registrando…" : "Primera validación"}
                  </button>
                  {primeras[evidencia.id]?.error && (
                    <p role="alert" data-testid={`error-primera-${evidencia.id}`} className="text-[11px] text-[var(--ui-error-texto)]">
                      {primeras[evidencia.id]?.error}
                    </p>
                  )}
                </div>
              )}
              {rol === "dpo" && pendiente && (
                <div className="space-y-1">
                  <button
                    type="button"
                    className={BOTON}
                    aria-disabled={!evidencia.primera_validacion_por || bloqueada}
                    aria-describedby={evidencia.primera_validacion_por ? undefined : id("final-ayuda")}
                    onClick={() => {
                      if (!evidencia.primera_validacion_por || bloqueada) return;
                      actualizarRevision(evidencia.id, { decision: "approved", aviso: null, error: null });
                    }}
                  >
                    Validación final
                  </button>
                  {!evidencia.primera_validacion_por && (
                    <p id={id("final-ayuda")} className="text-[11px] text-[var(--ui-texto-suave)]">
                      Disponible cuando el coordinador haga la primera validación
                    </p>
                  )}
                </div>
              )}
              {/* === fin RM-25c === */}

              {puedeValidarRol && pendiente && (
                <div className="space-y-2">
                  {bloqueada && (
                    <p
                      role="note"
                      data-testid={`cuatro-ojos-${evidencia.id}`}
                      className="flex items-start gap-2 text-[11px] text-[var(--ui-aviso-texto)]"
                    >
                      <Lock className="w-3.5 h-3.5 shrink-0 mt-0.5" aria-hidden="true" />
                      No puedes validar esta evidencia porque la subiste tú (regla de cuatro ojos). Debe validarla otra
                      persona.
                    </p>
                  )}
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className={BOTON}
                      disabled={bloqueada || revision.ocupada}
                      onClick={() => actualizarRevision(evidencia.id, { decision: "approved", aviso: null, error: null })}
                    >
                      Aprobar
                    </button>
                    <button
                      type="button"
                      className={BOTON}
                      disabled={bloqueada || revision.ocupada}
                      onClick={() => actualizarRevision(evidencia.id, { decision: "rejected", aviso: null, error: null })}
                    >
                      Rechazar
                    </button>
                  </div>

                  {revision.decision && !bloqueada && (
                    <form
                      aria-label={`${revision.decision === "approved" ? "Aprobar" : "Rechazar"} ${nombreDeArchivo(evidencia.clave_objeto)}`}
                      onSubmit={(e) => {
                        e.preventDefault();
                        void confirmarRevision(evidencia);
                      }}
                      className="space-y-2"
                    >
                      <label htmlFor={id("comentario")} className="block text-[11px] font-semibold text-[var(--ui-texto-suave)]">
                        {revision.decision === "rejected" ? "Motivo del rechazo (obligatorio)" : "Comentario (opcional)"}
                      </label>
                      <textarea
                        id={id("comentario")}
                        rows={2}
                        value={revision.comentario}
                        disabled={revision.ocupada}
                        onChange={(e) => actualizarRevision(evidencia.id, { comentario: e.target.value, aviso: null })}
                        className="w-full rounded-md bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] px-2.5 py-1.5 text-xs text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--ui-enlace)]"
                      />
                      {revision.aviso && (
                        <p role="alert" className="text-[11px] text-[var(--ui-error-texto)]">
                          {revision.aviso}
                        </p>
                      )}
                      <div className="flex gap-2">
                        <button type="submit" className={BOTON} disabled={revision.ocupada}>
                          {revision.ocupada ? "Enviando…" : revision.decision === "approved" ? "Confirmar aprobación" : "Confirmar rechazo"}
                        </button>
                        <button
                          type="button"
                          className={BOTON}
                          disabled={revision.ocupada}
                          onClick={() => setRevisiones((previo) => ({ ...previo, [evidencia.id]: REVISION_INICIAL }))}
                        >
                          Cancelar
                        </button>
                      </div>
                    </form>
                  )}

                  {revision.error && <BloqueError error={revision.error} testId={`error-validacion-${evidencia.id}`} />}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export default EvidenciaPanel;
