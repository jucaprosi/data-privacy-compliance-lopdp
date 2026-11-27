// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

import React, { useMemo, useRef, useState } from "react";
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
    return <FileSpreadsheet className="w-4 h-4 text-[var(--ui-exito-texto)] shrink-0" />;
  }
  if ([".json", ".xml", ".sql", ".md"].includes(ext)) {
    return <FileCode className="w-4 h-4 text-[var(--ui-info-texto)] shrink-0" />;
  }
  if ([".png", ".jpg", ".jpeg"].includes(ext)) {
    return <FileImage className="w-4 h-4 text-[var(--ui-aviso-texto)] shrink-0" />;
  }
  return <FileText className="w-4 h-4 text-[var(--ui-enlace)] shrink-0" />;
}

const ESTILO_AVISO: Record<TipoAviso, string> = {
  exito: "bg-[var(--ui-exito-fondo)] border-[var(--ui-exito-borde)] text-[var(--ui-exito-texto)]",
  duplicado: "bg-[var(--ui-aviso-fondo)] border-[var(--ui-aviso-borde)] text-[var(--ui-aviso-texto)]",
  error: "bg-[var(--ui-error-fondo)] border-[var(--ui-error-borde)] text-[var(--ui-error-texto)]",
};

function IconoAviso({ tipo }: { tipo: TipoAviso }) {
  if (tipo === "exito") return <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />;
  if (tipo === "duplicado") return <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />;
  return <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />;
}

export default function CargaEvidencias() {
  const normativaSeleccionada = useAuditStore((s) => s.normativaSeleccionada);
  const tamano = useAuditStore((s) => s.companyData.tamano);
  const perfil = useAuditStore((s) => s.companyData.perfil);
  const evidencias = useAuditStore((s) => s.evidencias);
  const vincularEvidencia = useAuditStore((s) => s.vincularEvidencia);
  const desvincularEvidencia = useAuditStore((s) => s.desvincularEvidencia);
  const eliminarEvidencia = useAuditStore((s) => s.eliminarEvidencia);
  // EVI-01b: con la subida firmada encendida, el servidor decide quién sube y quién vincula.
  const permisos = useAuditStore((s) => s.permisosEvidencia);
  const servidor = permisos?.subidaFirmada === true;
  const puedeSubir = !servidor || permisos?.rolQueSube != null;
  const puedeVincular = !servidor || permisos?.puedeVincular === true;

  // Una subida en curso ocupa la carga: soltar otro archivo mientras tanto se ignora (EVI-01b).
  const subiendo = useRef(false);
  const [enProceso, setEnProceso] = useState<ArchivoEnProceso[]>([]);
  const [avisos, setAvisos] = useState<Aviso[]>([]);
  const [confirmandoEliminar, setConfirmandoEliminar] = useState<string | null>(null);
  const [hashCopiado, setHashCopiado] = useState<string | null>(null);

  const normativa = resolverNormativa(normativaSeleccionada);
  const admiteVinculacion = usaBancoSGPDP(normativaSeleccionada);

  const gruposExigibles = useMemo(() => {
    const exigibles = podarBancoPorTamano(BANCO_PREGUNTAS, normalizarTamano(tamano), perfil);
    return DIMENSIONES_SGPDP.map((dimension) => ({
      dimension,
      controles: exigibles.filter((c) => c.dimensionId === dimension.id),
    })).filter((g) => g.controles.length > 0);
  }, [tamano, perfil]);

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
    if (servidor && subiendo.current) return;
    subiendo.current = true;
    try {
      await procesarLote(files);
    } finally {
      subiendo.current = false;
    }
  };

  const procesarLote = async (files: File[]) => {
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
            servidor
              ? `Documento registrado y comprobado. "${file.name}" quedó como ${resultado.evidencia.codigo}.`
              : `"${file.name}" registrado como ${resultado.evidencia.codigo}. Vincúlalo a los controles que respalda.`
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
    <div
      data-testid="carga-evidencias"
      className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-5 shadow-sm space-y-4"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[var(--ui-borde)] pb-2.5 gap-2">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--foreground)] flex items-center">
            <Fingerprint className="w-4 h-4 mr-1.5 text-[var(--ui-enlace)]" />
            Registro de Evidencias con Huella SHA-256
          </h3>
          <p className="text-[11px] text-[var(--ui-texto-suave)] mt-0.5">{normativa.descripcionArchivos}</p>
        </div>
        {evidencias.length > 0 && (
          <div className="flex items-center gap-2 text-[10px] font-mono shrink-0">
            <span className="px-2 py-0.5 rounded bg-[var(--ui-boton)] text-[var(--ui-texto-suave)] border border-[var(--ui-borde)]">
              {evidencias.length} registradas
            </span>
            {pendientes > 0 && (
              <span className="px-2 py-0.5 rounded bg-[var(--ui-aviso-fondo)] text-[var(--ui-aviso-texto)] border border-[var(--ui-aviso-borde)]">
                {pendientes} sin vincular
              </span>
            )}
          </div>
        )}
      </div>

      <div role="note" className="flex items-start gap-2 p-2.5 rounded-lg bg-[var(--ui-info-fondo)] border border-[var(--ui-info-borde)] text-[11px] text-[var(--ui-info-texto)] leading-relaxed">
        <ShieldCheck className="w-3.5 h-3.5 mt-0.5 shrink-0 text-[var(--ui-info-texto)]" />
        <span>
          {servidor
            ? "El documento se guarda en el almacén de tu organización. Al subirlo, el servidor comprueba que el archivo llegó completo (huella de integridad SHA-256); solo se registra si coincide con el que elegiste."
            : "El documento no sale de tu equipo: la huella SHA-256 se calcula en el navegador y solo se registran la huella, el nombre, el tamaño y los controles que respalda. Conserva el original para poder verificarlo más tarde."}
        </span>
      </div>

      {!puedeSubir && (
        <div
          role="note"
          data-testid="sin-permiso-subir"
          className="p-2.5 rounded-lg border border-[var(--ui-borde)] text-[11px] text-[var(--ui-texto-suave)]"
        >
          {permisos?.real
            ? "Con el diagnóstico real sellado, los documentos nuevos los suben el responsable de área o el coordinador; el DPO los valida."
            : "Hasta que se selle el diagnóstico real, los documentos los sube el DPO. Pídeselo si necesitas registrar uno."}
        </div>
      )}

      {puedeSubir && (
      <div
        {...getRootProps()}
        aria-busy={enProceso.length > 0}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition flex flex-col items-center justify-center space-y-2.5 ${
          isDragActive
            ? "border-[var(--ui-primario)] bg-[var(--ui-info-fondo)]"
            : "border-[var(--ui-borde-control)] hover:border-[var(--ui-primario)] bg-[var(--ui-superficie-2)]"
        }`}
      >
        <input {...getInputProps()} accept={normativa.accept} />
        <div className="w-10 h-10 rounded-full bg-[var(--ui-boton)] flex items-center justify-center">
          <UploadCloud className="w-5 h-5 text-[var(--ui-enlace)]" />
        </div>
        <div>
          <span className="text-xs font-semibold text-[var(--foreground)]">
            Haz clic para seleccionar o arrastra documentos aquí
          </span>
          <p className="text-[11px] text-[var(--ui-texto-suave)] mt-0.5">
            Formatos válidos para <strong className="text-[var(--foreground)]">{normativa.etiquetaCorta}</strong>:{" "}
            {normativa.extensiones.join(", ")} · máximo 50 MB por archivo
          </p>
        </div>
      </div>
      )}

      {enProceso.length > 0 && (
        <div className="space-y-1.5">
          {enProceso.map((p) => (
            <div
              key={p.clave}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[var(--ui-boton)] border border-[var(--ui-borde)] text-xs text-[var(--ui-texto-suave)]"
            >
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--ui-enlace)]" />
              <span className="truncate">{p.nombre}</span>
              <span role="status" className="text-[10px] text-[var(--ui-texto-suave)] shrink-0">
                {servidor ? "Subiendo y comprobando…" : "calculando huella…"}
              </span>
            </div>
          ))}
        </div>
      )}

      {avisos.length > 0 && (
        <div className="space-y-1.5" aria-live="polite">
          {avisos.map((aviso) => (
            <div
              key={aviso.id}
              role={aviso.tipo === "error" ? "alert" : undefined}
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
        <div className="divide-y divide-[var(--ui-borde)] border border-[var(--ui-borde)] rounded-lg overflow-hidden bg-[var(--ui-superficie)]">
          {evidencias.map((evidencia) => {
            const pendiente = evidencia.controlesVinculados.length === 0;
            const confirmando = confirmandoEliminar === evidencia.id;
            const vinculados = new Set(evidencia.controlesVinculados);

            return (
              <div
                key={evidencia.id}
                className={`px-3.5 py-3 text-xs space-y-2 border-l-2 ${
                  pendiente ? "border-l-[var(--ui-aviso-borde)]" : "border-l-[var(--ui-exito-borde)]"
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5 min-w-0">
                    {iconoArchivo(evidencia.nombreArchivo)}
                    <span className="font-mono font-bold text-[var(--ui-enlace)] shrink-0">{evidencia.codigo}</span>
                    <span className="font-medium text-[var(--foreground)] truncate" title={evidencia.nombreArchivo}>
                      {evidencia.nombreArchivo}
                    </span>
                    <span className="text-[10px] font-mono text-[var(--ui-texto-suave)] shrink-0">
                      {formatearTamano(evidencia.tamanoBytes)}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0 text-[10px] text-[var(--ui-texto-suave)]">
                    <button
                      type="button"
                      onClick={() => void copiarHash(evidencia)}
                      className="flex items-center gap-1 font-mono text-[var(--ui-texto-suave)] hover:text-[var(--ui-enlace)] cursor-pointer"
                      title={`SHA-256: ${evidencia.sha256}. Clic para copiar la huella completa.`}
                    >
                      {hashCopiado === evidencia.id ? (
                        <Check className="w-3 h-3 text-[var(--ui-exito-texto)]" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                      {hashCopiado === evidencia.id ? "Huella copiada" : abreviarHash(evidencia.sha256)}
                    </button>
                    <span className="font-mono">{formatearFechaRegistro(evidencia.registradaEn)}</span>
                    {servidor && evidencia.enServidor && (
                      <span
                        data-testid="evidencia-en-servidor"
                        className="inline-flex items-center gap-1 text-[var(--ui-exito-texto)] font-semibold"
                      >
                        <ShieldCheck className="w-3 h-3" />
                        Registrado y comprobado en el servidor
                      </span>
                    )}
                    {!confirmando && !evidencia.enServidor && (
                      <button
                        type="button"
                        onClick={() => setConfirmandoEliminar(evidencia.id)}
                        className="p-1 text-[var(--ui-peligro-texto)] hover:opacity-80 transition cursor-pointer"
                        title="Eliminar evidencia"
                        aria-label={`Eliminar ${evidencia.codigo}`}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>

                {confirmando && (
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded-lg bg-[var(--ui-error-fondo)] border border-[var(--ui-error-borde)] text-[var(--ui-error-texto)]">
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
                        className="px-2.5 py-1 rounded-md border border-[var(--ui-peligro-texto)] text-[var(--ui-peligro-texto)] font-semibold hover:bg-[var(--ui-error-fondo)] cursor-pointer"
                      >
                        Eliminar
                      </button>
                      <button
                        type="button"
                        onClick={() => setConfirmandoEliminar(null)}
                        className="px-2.5 py-1 rounded-md border border-[var(--ui-borde-control)] text-[var(--foreground)] hover:bg-[var(--ui-boton-hover)] cursor-pointer"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-1.5">
                  {pendiente ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-[var(--ui-aviso-fondo)] text-[var(--ui-aviso-texto)] border border-[var(--ui-aviso-borde)]">
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
                              ? "bg-[var(--ui-info-fondo)] text-[var(--ui-info-texto)] border-[var(--ui-info-borde)]"
                              : "bg-[var(--ui-boton)] text-[var(--ui-texto-suave)] border-[var(--ui-borde)] line-through"
                          }`}
                          title={exigible ? undefined : "Control no exigible para el tamaño de organización actual"}
                        >
                          {etiquetaControl(id)}
                          {puedeVincular && (
                          <button
                            type="button"
                            onClick={() => desvincularEvidencia(evidencia.id, id)}
                            className="p-0.5 rounded-full hover:bg-[var(--ui-boton-hover)] cursor-pointer"
                            aria-label={`Desvincular ${etiquetaControl(id)}`}
                            title="Desvincular"
                          >
                            <X className="w-2.5 h-2.5" />
                          </button>
                          )}
                        </span>
                      );
                    })
                  )}

                  {admiteVinculacion && !puedeVincular ? (
                    <span className="ml-auto text-[10px] text-[var(--ui-texto-suave)] italic">
                      {permisos?.real
                        ? "El diagnóstico real está sellado: los vínculos ya no cambian."
                        : "Solo el DPO vincula documentos a controles."}
                    </span>
                  ) : admiteVinculacion ? (
                    <label className="inline-flex items-center gap-1 ml-auto">
                      <Link2 className="w-3 h-3 text-[var(--ui-info-texto)]" />
                      <span className="sr-only">Vincular {evidencia.codigo} a un control</span>
                      <select
                        value=""
                        onChange={(e) => {
                          const id = Number.parseInt(e.target.value, 10);
                          if (Number.isFinite(id)) vincularEvidencia(evidencia.id, id);
                        }}
                        className="max-w-[16rem] text-[11px] rounded-md px-2 py-1 bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] text-[var(--foreground)] focus:outline-none focus:border-[var(--ui-primario)] cursor-pointer"
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
                    <span className="ml-auto text-[10px] text-[var(--ui-texto-suave)] italic">
                      La vinculación a controles aplica al assessment LOPDP.
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-3 text-[var(--ui-texto-suave)] text-xs italic">
          No hay evidencias registradas para {normativa.etiquetaCorta}. Al cambiar de normativa el registro se limpia.
        </div>
      )}
    </div>
  );
}
