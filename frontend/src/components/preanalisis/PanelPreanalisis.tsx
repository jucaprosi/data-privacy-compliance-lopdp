"use client";

import React, { useEffect, useRef, useState } from "react";
import { AlertCircle, FileSearch, Loader2, Sparkles, Upload, X } from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { calcularSha256, abreviarHash } from "@/lib/evidencias/hash";
import type { EvidenciaDocumental } from "@/lib/evidencias/tipos";
import { obtenerArchivo, recordarArchivo } from "@/lib/preanalisis/archivosSesion";
import {
  analizarControl,
  construirPropuesta,
  consultarEstadoServicio,
  ErrorPreanalisis,
  prepararDocumento,
} from "@/lib/preanalisis/cliente";
import type {
  ControlParaAnalisis,
  EstadoServicioIA,
  PreparacionDocumento,
  PropuestaIA,
} from "@/lib/preanalisis/tipos";
import ConsentimientoEnvio from "@/components/preanalisis/ConsentimientoEnvio";
import TarjetaPropuesta from "@/components/preanalisis/TarjetaPropuesta";

interface PanelPreanalisisProps {
  control: ControlParaAnalisis;
  onAplicar: (propuesta: PropuestaIA, modo: "aceptada" | "editada") => void;
}

type Accion = "analizar" | "ver";

interface SolicitudArchivo {
  evidencia: EvidenciaDocumental;
  accion: Accion;
}

interface ConsentimientoPendiente {
  evidencia: EvidenciaDocumental;
  preparacion: PreparacionDocumento;
}

interface VistaFragmentos {
  evidencia: EvidenciaDocumental;
  preparacion: PreparacionDocumento;
}

const EXTENSIONES_NO_ANALIZABLES = [".png", ".jpg", ".jpeg"];

const MENSAJE_FORMATO = "Este formato no puede analizarse automáticamente; respáldalo manualmente.";

function esFormatoNoAnalizable(nombre: string): boolean {
  const minuscula = nombre.toLowerCase();
  return EXTENSIONES_NO_ANALIZABLES.some((ext) => minuscula.endsWith(ext));
}

function mensajeDeError(error: unknown): string {
  if (error instanceof ErrorPreanalisis) return error.message;
  return error instanceof Error ? error.message : "Ocurrió un error inesperado.";
}

export default function PanelPreanalisis({ control, onAplicar }: PanelPreanalisisProps) {
  const evidenciasStore = useAuditStore((s) => s.evidencias);
  const propuesta = useAuditStore((s) => s.propuestasIA[control.control_id]);
  const respuestaActual = useAuditStore(
    (s) => s.respuestas.find((r) => r.preguntaId === control.control_id && !r.esReferencia)?.cumple
  );
  const guardarPropuestaIA = useAuditStore((s) => s.guardarPropuestaIA);
  const decidirPropuestaIA = useAuditStore((s) => s.decidirPropuestaIA);

  const evidencias = evidenciasStore.filter((e) => e.controlesVinculados.includes(control.control_id));

  const [estado, setEstado] = useState<EstadoServicioIA | null>(null);
  const [ocupada, setOcupada] = useState<string | null>(null);
  const [etapa, setEtapa] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [consentimiento, setConsentimiento] = useState<ConsentimientoPendiente | null>(null);
  const [vista, setVista] = useState<VistaFragmentos | null>(null);
  const [solicitud, setSolicitud] = useState<SolicitudArchivo | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const enCurso = useRef(false);

  useEffect(() => {
    let vigente = true;
    void consultarEstadoServicio().then((resultado) => {
      if (vigente) setEstado(resultado);
    });
    return () => {
      vigente = false;
    };
  }, []);

  const servicioDisponible = estado?.disponible === true;

  const ejecutar = async (evidencia: EvidenciaDocumental, accion: Accion, archivoPresentado?: File) => {
    if (enCurso.current) return;
    setError(null);
    setVista(null);

    if (esFormatoNoAnalizable(evidencia.nombreArchivo)) {
      setError(MENSAJE_FORMATO);
      return;
    }

    let archivo = archivoPresentado ?? obtenerArchivo(evidencia.sha256);
    if (!archivo) {
      setSolicitud({ evidencia, accion });
      inputRef.current?.click();
      return;
    }

    enCurso.current = true;
    setOcupada(evidencia.id);
    try {
      if (archivoPresentado) {
        setEtapa("Comprobando la huella del archivo…");
        const huella = await calcularSha256(archivoPresentado);
        if (huella !== evidencia.sha256.toLowerCase()) {
          setError(
            `El archivo presentado no coincide con ${evidencia.codigo}: su huella SHA-256 es distinta a la registrada. Presenta el documento original.`
          );
          return;
        }
        recordarArchivo(evidencia.sha256, archivoPresentado);
        archivo = archivoPresentado;
      }
      setEtapa("Buscando fragmentos relevantes…");
      const preparacion = await prepararDocumento(archivo, control);
      if (accion === "ver") {
        setVista({ evidencia, preparacion });
      } else {
        setConsentimiento({ evidencia, preparacion });
      }
    } catch (fallo) {
      setError(mensajeDeError(fallo));
    } finally {
      enCurso.current = false;
      setOcupada(null);
      setEtapa("");
    }
  };

  const alElegirArchivo = (evento: React.ChangeEvent<HTMLInputElement>) => {
    const archivo = evento.target.files?.[0];
    evento.target.value = "";
    const pendiente = solicitud;
    setSolicitud(null);
    if (archivo && pendiente) void ejecutar(pendiente.evidencia, pendiente.accion, archivo);
  };

  const confirmarEnvio = async () => {
    const pendiente = consentimiento;
    if (!pendiente || enCurso.current) return;
    setConsentimiento(null);
    enCurso.current = true;
    setOcupada(pendiente.evidencia.id);
    setEtapa("Analizando con IA…");
    setError(null);
    try {
      const resultado = await analizarControl(control, pendiente.preparacion.fragmentos);
      guardarPropuestaIA(construirPropuesta(resultado, pendiente.evidencia, control.control_id));
    } catch (fallo) {
      setError(mensajeDeError(fallo));
    } finally {
      enCurso.current = false;
      setOcupada(null);
      setEtapa("");
    }
  };

  const aplicar = (modo: "aceptada" | "editada") => {
    if (!propuesta) return;
    onAplicar(propuesta, modo);
    decidirPropuestaIA(control.control_id, modo);
  };

  return (
    <div className="bg-[#141417] border border-[#26262b] rounded-xl p-4 space-y-3 text-xs text-zinc-300">
      <div className="flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-[#9a3bf1]" />
        <h4 className="text-[11px] font-bold uppercase tracking-wider text-white">Pre-llenado asistido</h4>
        {estado?.disponible && (
          <span className="ml-auto text-[10px] font-mono text-zinc-500">
            {estado.proveedor} · {estado.modelo}
          </span>
        )}
      </div>
      <p className="text-[11px] text-zinc-400 leading-relaxed">
        La IA solo propone; nada se aplica sin tu decisión. Solo saldrán fragmentos enmascarados, y verás el texto exacto
        antes de autorizar el envío.
      </p>

      {estado === null && (
        <div className="flex items-center gap-2 text-[11px] text-zinc-500">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          Consultando el servicio de análisis…
        </div>
      )}

      {estado && !estado.disponible && (
        <div className="flex items-start gap-2 p-2.5 rounded-lg bg-[#ffab00]/10 border border-[#ffab00]/30 text-[11px] text-[#ffab00] leading-relaxed">
          <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>
            El análisis con IA no está disponible
            {estado.motivo ? `: ${estado.motivo}` : "."} Puedes ver los fragmentos relevantes de cada documento y
            responder manualmente.
          </span>
        </div>
      )}

      {evidencias.length === 0 ? (
        <p className="text-[11px] text-zinc-500 italic">
          Este control no tiene documentos vinculados. Vincula una evidencia para poder analizarla.
        </p>
      ) : (
        <ul className="divide-y divide-[#26262b] border border-[#26262b] rounded-lg bg-[#0a0a0c]">
          {evidencias.map((evidencia) => {
            const trabajando = ocupada === evidencia.id;
            const enSesion = obtenerArchivo(evidencia.sha256) !== undefined;
            return (
              <li key={evidencia.id} className="px-3 py-2 space-y-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono font-bold text-[#9a3bf1]">{evidencia.codigo}</span>
                  <span className="truncate text-zinc-200" title={evidencia.nombreArchivo}>
                    {evidencia.nombreArchivo}
                  </span>
                  <span className="text-[10px] font-mono text-zinc-500">{abreviarHash(evidencia.sha256)}</span>
                </div>
                {esFormatoNoAnalizable(evidencia.nombreArchivo) ? (
                  <p className="text-[11px] text-zinc-500">{MENSAJE_FORMATO}</p>
                ) : (
                  <div className="flex flex-wrap items-center gap-2">
                    {servicioDisponible && (
                      <button
                        type="button"
                        onClick={() => void ejecutar(evidencia, "analizar")}
                        disabled={ocupada !== null}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#9a3bf1] text-white font-semibold hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                      >
                        {trabajando ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
                        Analizar con IA
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => void ejecutar(evidencia, "ver")}
                      disabled={ocupada !== null}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md border border-[#3892f3]/50 text-[#3892f3] hover:bg-[#3892f3]/10 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                    >
                      <FileSearch className="w-3 h-3" />
                      Ver fragmentos relevantes
                    </button>
                    {!enSesion && (
                      <span className="inline-flex items-center gap-1 text-[10px] text-zinc-500">
                        <Upload className="w-3 h-3" />
                        Al usarlo se te pedirá volver a presentar el archivo
                      </span>
                    )}
                  </div>
                )}
                {trabajando && (
                  <div className="flex items-center gap-2 text-[11px] text-zinc-400" aria-live="polite">
                    <Loader2 className="w-3 h-3 animate-spin text-[#9a3bf1]" />
                    {etapa}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      <input
        ref={inputRef}
        type="file"
        className="hidden"
        onChange={alElegirArchivo}
        aria-label="Volver a presentar el archivo"
        tabIndex={-1}
      />

      {error && (
        <div
          role="alert"
          className="flex items-start gap-2 p-2.5 rounded-lg bg-[#ff1744]/10 border border-[#ff1744]/40 text-[11px] text-[#ff1744]"
        >
          <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span className="flex-1 leading-relaxed">{error}</span>
          <button type="button" onClick={() => setError(null)} aria-label="Cerrar aviso" className="cursor-pointer">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {vista && (
        <div className="border border-[#26262b] rounded-lg bg-[#0a0a0c] p-3 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
              Fragmentos relevantes de {vista.evidencia.codigo} (solo lectura, sin IA)
            </span>
            <button
              type="button"
              onClick={() => setVista(null)}
              aria-label="Cerrar fragmentos"
              className="ml-auto text-zinc-500 hover:text-white cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          {vista.preparacion.advertencias.map((advertencia, indice) => (
            <p key={indice} className="text-[11px] text-[#ffab00]">
              {advertencia}
            </p>
          ))}
          {vista.preparacion.fragmentos.length === 0 && (
            <p className="text-[11px] text-zinc-500 italic">No se encontraron fragmentos relevantes.</p>
          )}
          <ul className="space-y-1.5">
            {vista.preparacion.fragmentos.map((fragmento, indice) => (
              <li key={indice} className="p-2 rounded-lg bg-[#141417] border border-[#26262b] space-y-0.5">
                <div className="text-[10px] font-mono text-[#3892f3]">{fragmento.origen}</div>
                <p className="text-[11px] text-zinc-300 whitespace-pre-wrap break-words leading-relaxed">
                  {fragmento.texto}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {propuesta && (
        <TarjetaPropuesta
          propuesta={propuesta}
          respuestaActual={respuestaActual}
          onAceptar={() => aplicar("aceptada")}
          onEditar={() => aplicar("editada")}
          onDescartar={() => decidirPropuestaIA(control.control_id, "descartada")}
        />
      )}

      {consentimiento && (
        <ConsentimientoEnvio
          estadoServicio={estado}
          grupos={[
            {
              clave: consentimiento.evidencia.id,
              controlEtiqueta: `P${control.control_id} · ${control.control}`,
              documento: consentimiento.evidencia.codigo,
              fragmentos: consentimiento.preparacion.fragmentos,
              piiEnmascarada: consentimiento.preparacion.pii_enmascarada,
            },
          ]}
          onConfirmar={() => void confirmarEnvio()}
          onCancelar={() => setConsentimiento(null)}
        />
      )}
    </div>
  );
}
