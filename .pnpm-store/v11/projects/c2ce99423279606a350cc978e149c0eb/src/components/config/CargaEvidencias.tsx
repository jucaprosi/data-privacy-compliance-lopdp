"use client";

import React, { useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import {
  UploadCloud,
  FileText,
  FileSpreadsheet,
  FileCode,
  FileImage,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Trash2,
  Copy,
  Check,
  Link2,
  X,
  Loader2,
  Fingerprint,
  ShieldCheck,
} from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { extensionPermitida, resolverNormativa, usaBancoSGPDP } from "@/lib/normativas";
import {
  BANCO_PREGUNTAS,
  normalizarTamano,
  podarBancoPorTamano,
  type PreguntaAssessment,
} from "@/lib/bancoPreguntas";
import { DIMENSIONES_SGPDP } from "@/lib/dimensionesSGPDP";
import { abreviarHash, formatearFechaRegistro, formatearTamano } from "@/lib/evidencias/hash";
import { registrarArchivoComoEvidencia } from "@/lib/evidencias/registro";
import type { EvidenciaDocumental } from "@/lib/evidencias/tipos";

type TipoAviso = "exito" | "duplicado" | "error";

interface Aviso {
  id: number;
  tipo: TipoAviso;
  texto: string;
}

interface ArchivoEnProceso {
  clave: string;
  nombre: string;
}

const MAXIMO_AVISOS = 6;

const CONTROL_POR_ID: ReadonlyMap<number, PreguntaAssessment> = new Map(
  BANCO_PREGUNTAS.map((p) => [p.id, p])
);

function etiquetaControl(id: number): string {
  const control = CONTROL_POR_ID.get(id);
  return control ? `P${id} · ${control.control}` : `P${id}`;
}

function iconoArchivo(nombre: string) {
  const ext = "." + (nombre.split(".").pop() ?? "").toLowerCase();
  if ([".xlsx", ".csv", ".xbrl", ".ixbrl"].includes(ext)) {
    return <FileSpreadsheet className="w-4 h-4 text-[#00c853] shrink-0" />;
  }
  if ([".json", ".xml", ".sql", ".md"].includes(ext)) {
    return <FileCode className="w-4 h-4 text-[#3892f3] shrink-0" />;
  }
  if ([".png", ".jpg", ".jpeg"].includes(ext)) {
    return <FileImage className="w-4 h-4 text-[#ffab00] shrink-0" />;
  }
  return <FileText className="w-4 h-4 text-[#9a3bf1] shrink-0" />;
}

const ESTILO_AVISO: Record<TipoAviso, string> = {
  exito: "bg-[#00c853]/10 border-[#00c853]/40 text-[#00a846] dark:text-[#00c853]",
  duplicado: "bg-[#ffab00]/10 border-[#ffab00]/40 text-[#b37800] dark:text-[#ffab00]",
  error: "bg-[#ff1744]/10 border-[#ff1744]/40 text-[#ff1744]",
};

function IconoAviso({ tipo }: { tipo: TipoAviso }) {
  if (tipo === "exito") return <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />;
  if (tipo === "duplicado") return <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />;
  return <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />;
}

export default function CargaEvidencias() {
  const normativaSeleccionada = useAuditStore((s) => s.normativaSeleccionada);
  const tamano = useAuditStore((s) => s.companyData.tamano);
  const evidencias = useAuditStore((s) => s.evidencias);
  const vincularEvidencia = useAuditStore((s) => s.vincularEvidencia);
  const desvincularEvidencia = useAuditStore((s) => s.desvincularEvidencia);
  const eliminarEvidencia = useAuditStore((s) => s.eliminarEvidencia);

  const [enProceso, setEnProceso] = useState<ArchivoEnProceso[]>([]);
  const [avisos, setAvisos] = useState<Aviso[]>([]);
  const [confirmandoEliminar, setConfirmandoEliminar] = useState<string | null>(null);
  const [hashCopiado, setHashCopiado] = useState<string | null>(null);

  const normativa = resolverNormativa(normativaSeleccionada);
  const admiteVinculacion = usaBancoSGPDP(normativaSeleccionada);

  const gruposExigibles = useMemo(() => {
    const exigibles = podarBancoPorTamano(BANCO_PREGUNTAS, normalizarTamano(tamano));
    return DIMENSIONES_SGPDP.map((dimension) => ({
      dimension,
      controles: exigibles.filter((c) => c.dimensionId === dimension.id),
    })).filter((g) => g.controles.length > 0);
  }, [tamano]);

  const idsExigibles = useMemo(
    () => new Set(gruposExigibles.flatMap((g) => g.controles.map((c) => c.id))),
    [gruposExigibles]
  );

  const agregarAviso = (tipo: TipoAviso, texto: string) => {
    setAvisos((prev) =>
      [{ id: Date.now() + Math.random(), tipo, texto }, ...prev].slice(0, MAXIMO_AVISOS)
    );
  };

  const procesarArchivos = async (files: File[]) => {
    const validos = files.filter((f) => extensionPermitida(normativaSeleccionada, f.name));
    const rechazados = files.filter((f) => !validos.includes(f)).map((f) => f.name);

    if (rechazados.length > 0) {
      agregarAviso(
        "error",
        `Formato no admitido en ${rechazados.join(", ")}. Para ${normativa.etiquetaCorta} se aceptan: ${normativa.extensiones.join(", ")}.`
      );
    }

    // El registro calcula la huella de forma asíncrona: si la normativa cambia
    // mientras tanto, la evidencia ya no corresponde al régimen activo y se descarta.
    const normativaInicial = normativaSeleccionada;
    for (const file of validos) {
      if (useAuditStore.getState().normativaSeleccionada !== normativaInicial) break;
      const clave = `${file.name}-${file.size}-${file.lastModified}-${Math.random()}`;
      setEnProceso((prev) => [...prev, { clave, nombre: file.name }]);
      try {
        const resultado = await registrarArchivoComoEvidencia(file);
        if (useAuditStore.getState().normativaSeleccionada !== normativaInicial) break;
        if (!resultado.ok) {
          agregarAviso("error", resultado.error);
        } else if (resultado.duplicada) {
          const { evidencia } = resultado;
          agregarAviso(
            "duplicado",
            `"${file.name}" ya estaba registrado como ${evidencia.codigo} (${evidencia.nombreArchivo}): su contenido es idéntico.`
          );
        } else {
          agregarAviso(
            "exito",
            `"${file.name}" registrado como ${resultado.evidencia.codigo}. Vincúlalo a los controles que respalda.`
          );
        }
      } finally {
        setEnProceso((prev) => prev.filter((p) => p.clave !== clave));
      }
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) void procesarArchivos(acceptedFiles);
    },
  });

  const copiarHash = async (evidencia: EvidenciaDocumental) => {
    try {
      await navigator.clipboard.writeText(evidencia.sha256);
      setHashCopiado(evidencia.id);
      window.setTimeout(
        () => setHashCopiado((actual) => (actual === evidencia.id ? null : actual)),
        1800
      );
    } catch {
      agregarAviso(
        "error",
        `No se pudo copiar la huella de ${evidencia.codigo}. Huella completa: ${evidencia.sha256}`
      );
    }
  };

  const pendientes = evidencias.filter((e) => e.controlesVinculados.length === 0).length;

  return (
    <div className="bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-zinc-200 dark:border-[#26262b] pb-2.5 gap-2">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-900 dark:text-white flex items-center">
            <Fingerprint className="w-4 h-4 mr-1.5 text-[#9a3bf1]" />
            Registro de Evidencias con Huella SHA-256
          </h3>
          <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">{normativa.descripcionArchivos}</p>
        </div>
        {evidencias.length > 0 && (
          <div className="flex items-center gap-2 text-[10px] font-mono shrink-0">
            <span className="px-2 py-0.5 rounded bg-zinc-100 dark:bg-[#1e1e24] text-zinc-600 dark:text-zinc-300 border border-zinc-200 dark:border-[#26262b]">
              {evidencias.length} registradas
            </span>
            {pendientes > 0 && (
              <span className="px-2 py-0.5 rounded bg-[#ffab00]/10 text-[#b37800] dark:text-[#ffab00] border border-[#ffab00]/30">
                {pendientes} sin vincular
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex items-start gap-2 p-2.5 rounded-lg bg-[#3892f3]/5 border border-[#3892f3]/25 text-[11px] text-zinc-600 dark:text-zinc-300 leading-relaxed">
        <ShieldCheck className="w-3.5 h-3.5 mt-0.5 shrink-0 text-[#3892f3]" />
        <span>
          El documento no sale de tu equipo: la huella SHA-256 se calcula en el navegador y solo se registran la huella,
          el nombre, el tamaño y los controles que respalda. Conserva el original para poder verificarlo más tarde.
        </span>
      </div>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition flex flex-col items-center justify-center space-y-2.5 ${
          isDragActive
            ? "border-[#9a3bf1] bg-[#9a3bf1]/10"
            : "border-zinc-300 dark:border-[#26262b] hover:border-[#9a3bf1]/60 bg-zinc-50 dark:bg-[#0a0a0c]"
        }`}
      >
        <input {...getInputProps()} accept={normativa.accept} />
        <div className="w-10 h-10 rounded-full bg-zinc-100 dark:bg-[#1e1e24] flex items-center justify-center">
          <UploadCloud className="w-5 h-5 text-[#9a3bf1]" />
        </div>
        <div>
          <span className="text-xs font-semibold text-zinc-900 dark:text-white">
            Haz clic para seleccionar o arrastra documentos aquí
          </span>
          <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">
            Formatos válidos para <strong className="text-zinc-800 dark:text-zinc-200">{normativa.etiquetaCorta}</strong>:{" "}
            {normativa.extensiones.join(", ")} · máximo 50 MB por archivo
          </p>
        </div>
      </div>

      {enProceso.length > 0 && (
        <div className="space-y-1.5">
          {enProceso.map((p) => (
            <div
              key={p.clave}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-zinc-50 dark:bg-[#1e1e24] border border-zinc-200 dark:border-[#26262b] text-xs text-zinc-600 dark:text-zinc-300"
            >
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#9a3bf1]" />
              <span className="truncate">{p.nombre}</span>
              <span className="text-[10px] text-zinc-500 shrink-0">calculando huella…</span>
            </div>
          ))}
        </div>
      )}

      {avisos.length > 0 && (
        <div className="space-y-1.5" aria-live="polite">
          {avisos.map((aviso) => (
            <div
              key={aviso.id}
              className={`flex items-start gap-2.5 p-2.5 rounded-lg border text-xs ${ESTILO_AVISO[aviso.tipo]}`}
            >
              <IconoAviso tipo={aviso.tipo} />
              <span className="flex-1 leading-relaxed break-words">{aviso.texto}</span>
              <button
                type="button"
                onClick={() => setAvisos((prev) => prev.filter((a) => a.id !== aviso.id))}
                className="opacity-70 hover:opacity-100 cursor-pointer"
                aria-label="Cerrar aviso"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {evidencias.length > 0 ? (
        <div className="divide-y divide-zinc-200 dark:divide-[#26262b] border border-zinc-200 dark:border-[#26262b] rounded-lg overflow-hidden bg-white dark:bg-[#0a0a0c]">
          {evidencias.map((evidencia) => {
            const pendiente = evidencia.controlesVinculados.length === 0;
            const confirmando = confirmandoEliminar === evidencia.id;
            const vinculados = new Set(evidencia.controlesVinculados);

            return (
              <div
                key={evidencia.id}
                className={`px-3.5 py-3 text-xs space-y-2 border-l-2 ${
                  pendiente ? "border-l-[#ffab00]" : "border-l-[#00c853]"
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5 min-w-0">
                    {iconoArchivo(evidencia.nombreArchivo)}
                    <span className="font-mono font-bold text-[#9a3bf1] shrink-0">{evidencia.codigo}</span>
                    <span className="font-medium text-zinc-900 dark:text-zinc-100 truncate" title={evidencia.nombreArchivo}>
                      {evidencia.nombreArchivo}
                    </span>
                    <span className="text-[10px] font-mono text-zinc-500 shrink-0">
                      {formatearTamano(evidencia.tamanoBytes)}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0 text-[10px] text-zinc-500">
                    <button
                      type="button"
                      onClick={() => void copiarHash(evidencia)}
                      className="flex items-center gap-1 font-mono text-zinc-600 dark:text-zinc-400 hover:text-[#3892f3] cursor-pointer"
                      title={`SHA-256: ${evidencia.sha256}. Clic para copiar la huella completa.`}
                    >
                      {hashCopiado === evidencia.id ? (
                        <Check className="w-3 h-3 text-[#00c853]" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                      {hashCopiado === evidencia.id ? "Huella copiada" : abreviarHash(evidencia.sha256)}
                    </button>
                    <span className="font-mono">{formatearFechaRegistro(evidencia.registradaEn)}</span>
                    {!confirmando && (
                      <button
                        type="button"
                        onClick={() => setConfirmandoEliminar(evidencia.id)}
                        className="p-1 text-[#ff1744] hover:opacity-80 transition cursor-pointer"
                        title="Eliminar evidencia"
                        aria-label={`Eliminar ${evidencia.codigo}`}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>

                {confirmando && (
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded-lg bg-[#ff1744]/10 border border-[#ff1744]/40 text-[#ff1744]">
                    <span className="leading-relaxed">
                      ¿Eliminar {evidencia.codigo} del registro?
                      {evidencia.controlesVinculados.length > 0
                        ? ` Dejará de respaldar ${evidencia.controlesVinculados.length} control(es).`
                        : ""}
                    </span>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => {
                          eliminarEvidencia(evidencia.id);
                          setConfirmandoEliminar(null);
                        }}
                        className="px-2.5 py-1 rounded-md bg-[#ff1744] text-white font-semibold hover:opacity-90 cursor-pointer"
                      >
                        Eliminar
                      </button>
                      <button
                        type="button"
                        onClick={() => setConfirmandoEliminar(null)}
                        className="px-2.5 py-1 rounded-md border border-zinc-300 dark:border-[#26262b] text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-[#1e1e24] cursor-pointer"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-1.5">
                  {pendiente ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#ffab00]/10 text-[#b37800] dark:text-[#ffab00] border border-[#ffab00]/30">
                      <AlertTriangle className="w-3 h-3" />
                      Pendiente de vincular · aún no respalda ningún control
                    </span>
                  ) : (
                    evidencia.controlesVinculados.map((id) => {
                      const exigible = idsExigibles.has(id);
                      return (
                        <span
                          key={id}
                          className={`inline-flex items-center gap-1 pl-2 pr-1 py-0.5 rounded-full text-[10px] font-medium border ${
                            exigible
                              ? "bg-[#9a3bf1]/10 text-[#7b22d0] dark:text-[#c89bf7] border-[#9a3bf1]/30"
                              : "bg-zinc-100 dark:bg-[#1e1e24] text-zinc-500 border-zinc-200 dark:border-[#26262b] line-through"
                          }`}
                          title={exigible ? undefined : "Control no exigible para el tamaño de organización actual"}
                        >
                          {etiquetaControl(id)}
                          <button
                            type="button"
                            onClick={() => desvincularEvidencia(evidencia.id, id)}
                            className="p-0.5 rounded-full hover:bg-black/10 dark:hover:bg-white/10 cursor-pointer"
                            aria-label={`Desvincular ${etiquetaControl(id)}`}
                            title="Desvincular"
                          >
                            <X className="w-2.5 h-2.5" />
                          </button>
                        </span>
                      );
                    })
                  )}

                  {admiteVinculacion ? (
                    <label className="inline-flex items-center gap-1 ml-auto">
                      <Link2 className="w-3 h-3 text-[#3892f3]" />
                      <span className="sr-only">Vincular {evidencia.codigo} a un control</span>
                      <select
                        value=""
                        onChange={(e) => {
                          const id = Number.parseInt(e.target.value, 10);
                          if (Number.isFinite(id)) vincularEvidencia(evidencia.id, id);
                        }}
                        className="max-w-[16rem] text-[11px] rounded-md px-2 py-1 bg-zinc-50 dark:bg-[#1e1e24] border border-zinc-200 dark:border-[#26262b] text-zinc-700 dark:text-zinc-200 focus:outline-none focus:border-[#3892f3] cursor-pointer"
                      >
                        <option value="" disabled>
                          Vincular a control…
                        </option>
                        {gruposExigibles.map(({ dimension, controles }) => {
                          const disponibles = controles.filter((c) => !vinculados.has(c.id));
                          if (disponibles.length === 0) return null;
                          return (
                            <optgroup key={dimension.id} label={`${dimension.id} · ${dimension.nombre}`}>
                              {disponibles.map((c) => (
                                <option key={c.id} value={c.id} title={c.enunciadoVigente}>
                                  {`P${c.id} · ${c.control}`}
                                </option>
                              ))}
                            </optgroup>
                          );
                        })}
                      </select>
                    </label>
                  ) : (
                    <span className="ml-auto text-[10px] text-zinc-500 italic">
                      La vinculación a controles aplica al assessment LOPDP.
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-3 text-zinc-500 text-xs italic">
          No hay evidencias registradas para {normativa.etiquetaCorta}. Al cambiar de normativa el registro se limpia.
        </div>
      )}
    </div>
  );
}
