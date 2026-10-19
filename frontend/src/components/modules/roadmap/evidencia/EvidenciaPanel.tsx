"use client";

import React, { useCallback, useEffect, useId, useMemo, useState } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";
import { AlertCircle, CheckCircle2, CircleDashed, Loader2, Lock, UploadCloud, XCircle } from "lucide-react";

import { formatearTamano } from "@/lib/evidencias/hash";
import { roadmapApi } from "@/lib/roadmap/cliente";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import { ApiError } from "@/types/roadmap";
import type { EvidenceValidationStatus, TaskEvidence } from "@/types/roadmap";
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

const REVISION_INICIAL: Revision = { decision: null, comentario: "", ocupada: false, aviso: null, error: null };

const ESTADO_VALIDACION: Record<EvidenceValidationStatus, { texto: string; clase: string; icono: React.ReactNode }> = {
  pending: {
    texto: "Pendiente de validación",
    clase: "border-[#ffb300]/60 text-[#ffd166]",
    icono: <CircleDashed className="w-3.5 h-3.5" aria-hidden="true" />,
  },
  approved: {
    texto: "Aprobada",
    clase: "border-[#00c853]/60 text-[#5fe39a]",
    icono: <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />,
  },
  rejected: {
    texto: "Rechazada",
    clase: "border-[#ff1744]/60 text-[#ff7b92]",
    icono: <XCircle className="w-3.5 h-3.5" aria-hidden="true" />,
  },
};

const BOTON =
  "inline-flex items-center gap-1.5 rounded-md border border-[#26262b] bg-[#1b1b20] px-2.5 py-1.5 text-xs " +
  "font-semibold text-zinc-100 hover:bg-[#23232a] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#3892f3] " +
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
    <div role="alert" data-testid={testId} className="flex items-start gap-2 p-2.5 rounded-md bg-[#ff1744]/10 border border-[#ff1744]/40 text-xs">
      <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[#ff1744]" aria-hidden="true" />
      <div className="space-y-0.5">
        <p>{error.mensaje}</p>
        {error.codigo && <p className="text-zinc-400">Código: {error.codigo}</p>}
        {error.accion && <p className="text-zinc-400">Acción requerida: {error.accion}</p>}
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

  const visibles = evidencias.filter((e) => evidenciaVisible(rol, usuarioId, e));

  return (
    <section aria-label="Evidencia de la tarea" className="bg-[#141417] border border-[#26262b] rounded-xl p-5 space-y-4 text-zinc-200">
      <header>
        <h2 className="text-sm font-bold uppercase tracking-wider text-white">Evidencia</h2>
        {titulo && <p className="text-[11px] text-zinc-400 mt-0.5">{titulo}</p>}
      </header>

      {puedeSubirRol ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition flex flex-col items-center gap-2 ${
            isDragActive ? "border-[#3892f3] bg-[#3892f3]/10" : "border-[#26262b] hover:border-[#3892f3]/60"
          } ${subiendo ? "opacity-60 cursor-not-allowed" : ""}`}
        >
          <input {...getInputProps({ "aria-label": "Archivo de evidencia" })} />
          <UploadCloud className="w-5 h-5 text-[#3892f3]" aria-hidden="true" />
          <p className="text-xs font-semibold text-white">Suelta aquí el archivo o haz clic para elegirlo</p>
          <p className="text-[11px] text-zinc-400">
            Se admiten {EXTENSIONES_PERMITIDAS.join(", ")} de hasta {formatearTamano(TAMANO_MAXIMO_BYTES)}.
          </p>
        </div>
      ) : (
        <div role="note" className="flex items-start gap-2.5 p-3 rounded-lg bg-[#ffb300]/10 border border-[#ffb300]/40 text-xs">
          <Lock className="w-4 h-4 shrink-0 mt-0.5 text-[#ffb300]" aria-hidden="true" />
          <p>
            Tu rol actual es <strong>{rol}</strong> y no sube evidencia. Solo la suben el responsable de área y el
            coordinador.
          </p>
        </div>
      )}

      {rechazos.length > 0 && (
        <ul role="alert" data-testid="rechazos" className="space-y-1 text-xs text-[#ff7b92]">
          {rechazos.map((mensaje) => (
            <li key={mensaje}>{mensaje}</li>
          ))}
        </ul>
      )}

      {subiendo && paso && (
        <div role="status" aria-live="polite" className="flex items-center gap-2.5 p-3 rounded-lg bg-[#3892f3]/10 border border-[#3892f3]/40 text-xs">
          <Loader2 className="w-4 h-4 animate-spin text-[#3892f3]" aria-hidden="true" />
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
        <p className="text-[11px] text-zinc-500">Como responsable de área, aquí solo ves la evidencia que subiste tú.</p>
      )}

      {cargando && (
        <p role="status" className="flex items-center gap-2 text-xs text-zinc-300">
          <Loader2 className="w-4 h-4 animate-spin text-[#3892f3]" aria-hidden="true" />
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
        <p role="status" data-testid="sin-evidencia" className="text-xs text-zinc-400">
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
              className="rounded-lg bg-[#0a0a0c] border border-[#26262b] p-4 space-y-2.5"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-white break-all">{nombreDeArchivo(evidencia.r2_key)}</p>
                  <p className="text-[11px] text-zinc-500 mt-0.5">
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
                <p className="text-xs text-zinc-300">
                  <span className="text-zinc-500">Comentario:</span> {evidencia.notes}
                </p>
              )}

              {puedeValidarRol && pendiente && (
                <div className="space-y-2">
                  {bloqueada && (
                    <p
                      role="note"
                      data-testid={`cuatro-ojos-${evidencia.id}`}
                      className="flex items-start gap-2 text-[11px] text-[#ffd166]"
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
                      aria-label={`${revision.decision === "approved" ? "Aprobar" : "Rechazar"} ${nombreDeArchivo(evidencia.r2_key)}`}
                      onSubmit={(e) => {
                        e.preventDefault();
                        void confirmarRevision(evidencia);
                      }}
                      className="space-y-2"
                    >
                      <label htmlFor={id("comentario")} className="block text-[11px] font-semibold text-zinc-300">
                        {revision.decision === "rejected" ? "Motivo del rechazo (obligatorio)" : "Comentario (opcional)"}
                      </label>
                      <textarea
                        id={id("comentario")}
                        rows={2}
                        value={revision.comentario}
                        disabled={revision.ocupada}
                        onChange={(e) => actualizarRevision(evidencia.id, { comentario: e.target.value, aviso: null })}
                        className="w-full rounded-md bg-[#0a0a0c] border border-[#26262b] px-2.5 py-1.5 text-xs text-zinc-100 focus:outline-none focus:ring-2 focus:ring-[#3892f3]"
                      />
                      {revision.aviso && (
                        <p role="alert" className="text-[11px] text-[#ff6b86]">
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
