"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { AlertCircle, CheckCircle2, Loader2, Sparkles, X } from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { BANCO_PREGUNTAS, normalizarTamano, podarBancoPorTamano } from "@/lib/bancoPreguntas";
import type { EvidenciaDocumental } from "@/lib/evidencias/tipos";
import { obtenerArchivo } from "@/lib/preanalisis/archivosSesion";
import {
  analizarControl,
  construirPropuesta,
  consultarEstadoServicio,
  ErrorPreanalisis,
  prepararDocumento,
} from "@/lib/preanalisis/cliente";
import type { ControlParaAnalisis, EstadoServicioIA, PreparacionDocumento } from "@/lib/preanalisis/tipos";
import ConsentimientoEnvio, { type GrupoConsentimiento } from "@/components/preanalisis/ConsentimientoEnvio";

interface PrellenadoMasivoProps {
  onTerminar?: () => void;
}

interface ParAnalisis {
  control: ControlParaAnalisis;
  evidencia: EvidenciaDocumental;
  archivo: File;
}

interface ParPreparado extends ParAnalisis {
  preparacion: PreparacionDocumento;
}

interface Resumen {
  conSustento: number;
  sinSustento: number;
  errores: string[];
  cancelado: boolean;
}

type Fase = "reposo" | "preparando" | "consentimiento" | "analizando" | "resumen";

const CONCURRENCIA_PREPARACION = 2;
const EXTENSIONES_NO_ANALIZABLES = [".png", ".jpg", ".jpeg"];

function esAnalizable(nombre: string): boolean {
  const minuscula = nombre.toLowerCase();
  return !EXTENSIONES_NO_ANALIZABLES.some((ext) => minuscula.endsWith(ext));
}

function mensajeDeError(error: unknown): string {
  if (error instanceof ErrorPreanalisis) return error.message;
  return error instanceof Error ? error.message : "Error inesperado.";
}

export default function PrellenadoMasivo({ onTerminar }: PrellenadoMasivoProps) {
  const evidencias = useAuditStore((s) => s.evidencias);
  const tamano = useAuditStore((s) => s.companyData.tamano);
  const perfil = useAuditStore((s) => s.companyData.perfil);
  const guardarPropuestaIA = useAuditStore((s) => s.guardarPropuestaIA);
  const propuestasIA = useAuditStore((s) => s.propuestasIA);

  const [estado, setEstado] = useState<EstadoServicioIA | null>(null);
  const [fase, setFase] = useState<Fase>("reposo");
  const [progreso, setProgreso] = useState({ hecho: 0, total: 0 });
  const [preparados, setPreparados] = useState<ParPreparado[]>([]);
  const [sinArchivo, setSinArchivo] = useState<string[]>([]);
  const [erroresPreparacion, setErroresPreparacion] = useState<string[]>([]);
  const [resumen, setResumen] = useState<Resumen | null>(null);

  const cancelado = useRef(false);
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

  const controles = useMemo<ControlParaAnalisis[]>(
    () =>
      podarBancoPorTamano(BANCO_PREGUNTAS, normalizarTamano(tamano), perfil)
        .filter((c) => evidencias.some((e) => e.controlesVinculados.includes(c.id)))
        // Lo que el auditor ya aceptó o editó es una decisión suya: el lote no lo
        // vuelve a analizar ni lo reemplaza por una propuesta nueva.
        .filter((c) => {
          const decision = propuestasIA[c.id]?.decision;
          return decision !== "aceptada" && decision !== "editada";
        })
        .map((c) => ({
          control_id: c.id,
          control: c.control,
          enunciado: c.enunciadoVigente,
          evidencia_esperada: c.evidenciaVigente,
          referencia_normativa: c.referenciaNormativa,
        })),
    [evidencias, tamano, perfil, propuestasIA]
  );

  const disponible = estado?.disponible === true;
  const ocupado = fase !== "reposo" && fase !== "resumen";

  const cerrar = () => {
    setFase("reposo");
    setResumen(null);
    setPreparados([]);
    setSinArchivo([]);
    setErroresPreparacion([]);
    onTerminar?.();
  };

  const iniciar = async () => {
    if (enCurso.current || !disponible) return;
    enCurso.current = true;
    cancelado.current = false;
    setResumen(null);
    setErroresPreparacion([]);

    const pares: ParAnalisis[] = [];
    const faltantes: string[] = [];
    for (const control of controles) {
      const candidatas = evidencias.filter(
        (e) => e.controlesVinculados.includes(control.control_id) && esAnalizable(e.nombreArchivo)
      );
      let elegido: ParAnalisis | null = null;
      for (const evidencia of candidatas) {
        const archivo = obtenerArchivo(evidencia.sha256);
        if (archivo) {
          elegido = { control, evidencia, archivo };
          break;
        }
      }
      if (elegido) pares.push(elegido);
      else if (candidatas.length > 0) faltantes.push(`P${control.control_id} · ${control.control}`);
    }
    setSinArchivo(faltantes);

    if (pares.length === 0) {
      setPreparados([]);
      setResumen({ conSustento: 0, sinSustento: 0, errores: [], cancelado: false });
      setFase("resumen");
      enCurso.current = false;
      return;
    }

    setFase("preparando");
    setProgreso({ hecho: 0, total: pares.length });
    const listos: ParPreparado[] = [];
    const errores: string[] = [];
    let siguiente = 0;
    let hechos = 0;

    const trabajador = async () => {
      while (!cancelado.current) {
        const indice = siguiente++;
        if (indice >= pares.length) return;
        const par = pares[indice];
        try {
          const preparacion = await prepararDocumento(par.archivo, par.control);
          listos[indice] = { ...par, preparacion };
        } catch (fallo) {
          errores.push(`P${par.control.control_id} · ${par.evidencia.codigo}: ${mensajeDeError(fallo)}`);
        }
        hechos += 1;
        setProgreso({ hecho: hechos, total: pares.length });
      }
    };
    await Promise.all(Array.from({ length: CONCURRENCIA_PREPARACION }, () => trabajador()));

    const utiles = listos.filter((p): p is ParPreparado => p !== undefined && p.preparacion.fragmentos.length > 0);
    for (const par of listos) {
      if (par && par.preparacion.fragmentos.length === 0) {
        errores.push(`P${par.control.control_id} · ${par.evidencia.codigo}: no se encontraron fragmentos relevantes.`);
      }
    }
    setErroresPreparacion(errores);
    enCurso.current = false;

    if (cancelado.current || utiles.length === 0) {
      setResumen({ conSustento: 0, sinSustento: 0, errores, cancelado: cancelado.current });
      setFase("resumen");
      return;
    }
    setPreparados(utiles);
    setFase("consentimiento");
  };

  const confirmarLote = async () => {
    if (enCurso.current) return;
    enCurso.current = true;
    cancelado.current = false;
    setFase("analizando");
    setProgreso({ hecho: 0, total: preparados.length });

    let conSustento = 0;
    let sinSustento = 0;
    const errores = [...erroresPreparacion];
    let hechos = 0;
    for (const par of preparados) {
      if (cancelado.current) break;
      try {
        const resultado = await analizarControl(par.control, par.preparacion.fragmentos);
        if (cancelado.current) break;
        guardarPropuestaIA(construirPropuesta(resultado, par.evidencia, par.control.control_id));
        if (resultado.estado === "Sin sustento") sinSustento += 1;
        else conSustento += 1;
      } catch (fallo) {
        errores.push(`P${par.control.control_id} · ${par.evidencia.codigo}: ${mensajeDeError(fallo)}`);
        if (fallo instanceof ErrorPreanalisis && (fallo.status === 503 || fallo.status === 0)) break;
      }
      hechos += 1;
      setProgreso({ hecho: hechos, total: preparados.length });
    }
    enCurso.current = false;
    setResumen({ conSustento, sinSustento, errores, cancelado: cancelado.current });
    setFase("resumen");
  };

  const grupos: GrupoConsentimiento[] = preparados.map((p) => ({
    clave: `${p.control.control_id}-${p.evidencia.id}`,
    controlEtiqueta: `P${p.control.control_id} · ${p.control.control}`,
    documento: p.evidencia.codigo,
    fragmentos: p.preparacion.fragmentos,
    piiEnmascarada: p.preparacion.pii_enmascarada,
  }));

  const porcentaje = progreso.total > 0 ? Math.round((progreso.hecho / progreso.total) * 100) : 0;

  return (
    <>
      <div className="inline-flex flex-col items-start gap-0.5">
        <button
          type="button"
          onClick={() => void iniciar()}
          disabled={!disponible || ocupado || controles.length === 0}
          title={!disponible ? (estado?.motivo ?? "Consultando el servicio de análisis…") : undefined}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#9a3bf1] text-white text-xs font-semibold hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >
          {ocupado ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
          Pre-llenar con IA ({controles.length})
        </button>
        {estado && !estado.disponible && (
          <span className="text-[10px] text-[#ffab00] max-w-xs leading-snug">
            {estado.motivo ?? "El análisis con IA no está disponible."}
          </span>
        )}
      </div>

      {(fase === "preparando" || fase === "analizando") && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70">
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Progreso del pre-llenado"
            className="w-full max-w-md bg-[#141417] border border-[#26262b] rounded-xl p-5 space-y-3 text-xs text-zinc-300"
          >
            <div className="flex items-center gap-2 text-white font-bold uppercase tracking-wider text-[11px]">
              <Loader2 className="w-4 h-4 animate-spin text-[#9a3bf1]" />
              {fase === "preparando" ? "Preparando documentos" : "Analizando con IA"}
            </div>
            <div
              className="h-2 rounded-full bg-[#1e1e24] overflow-hidden"
              role="progressbar"
              aria-valuemin={0}
              aria-valuemax={progreso.total}
              aria-valuenow={progreso.hecho}
            >
              <div className="h-full bg-[#9a3bf1] transition-all" style={{ width: `${porcentaje}%` }} />
            </div>
            <div className="text-[11px] font-mono text-zinc-400">
              {progreso.hecho} de {progreso.total}
            </div>
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => {
                  cancelado.current = true;
                }}
                className="px-3 py-1.5 rounded-md border border-[#26262b] text-zinc-300 hover:bg-[#1e1e24] cursor-pointer"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {fase === "consentimiento" && (
        <ConsentimientoEnvio
          modoLote
          grupos={grupos}
          estadoServicio={estado}
          onConfirmar={() => void confirmarLote()}
          onCancelar={cerrar}
        />
      )}

      {fase === "resumen" && resumen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70">
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Resumen del pre-llenado"
            className="w-full max-w-lg max-h-[90vh] overflow-y-auto bg-[#141417] border border-[#26262b] rounded-xl p-5 space-y-3 text-xs text-zinc-300"
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#00c853]" />
              <h2 className="text-[11px] font-bold uppercase tracking-wider text-white">
                {resumen.cancelado ? "Pre-llenado cancelado" : "Pre-llenado terminado"}
              </h2>
              <button
                type="button"
                onClick={cerrar}
                aria-label="Cerrar resumen"
                className="ml-auto text-zinc-500 hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <ul className="space-y-1 text-[11px]">
              <li>
                Propuestas con sustento: <span className="font-mono font-bold text-[#00c853]">{resumen.conSustento}</span>
              </li>
              <li>
                Propuestas sin sustento: <span className="font-mono font-bold text-zinc-200">{resumen.sinSustento}</span>
              </li>
              <li>
                Errores: <span className="font-mono font-bold text-[#ff1744]">{resumen.errores.length}</span>
              </li>
            </ul>
            <p className="text-[11px] text-zinc-400 leading-relaxed">
              Todas las propuestas quedan pendientes: revísalas una a una en cada pregunta. Nada se aplicó todavía.
            </p>
            {sinArchivo.length > 0 && (
              <div className="p-2.5 rounded-lg bg-[#ffab00]/10 border border-[#ffab00]/30 text-[11px] text-[#ffab00] space-y-1">
                <div className="font-semibold">Requieren volver a presentar el archivo ({sinArchivo.length})</div>
                <ul className="list-disc pl-4 text-[#ffab00]/90">
                  {sinArchivo.map((etiqueta) => (
                    <li key={etiqueta}>{etiqueta}</li>
                  ))}
                </ul>
              </div>
            )}
            {resumen.errores.length > 0 && (
              <div className="p-2.5 rounded-lg bg-[#ff1744]/10 border border-[#ff1744]/40 text-[11px] text-[#ff1744] space-y-1">
                <div className="flex items-center gap-1 font-semibold">
                  <AlertCircle className="w-3.5 h-3.5" />
                  Detalle de errores
                </div>
                <ul className="list-disc pl-4">
                  {resumen.errores.map((texto, indice) => (
                    <li key={indice}>{texto}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="flex justify-end">
              <button
                type="button"
                onClick={cerrar}
                className="px-3 py-1.5 rounded-md bg-[#9a3bf1] text-white font-semibold hover:opacity-90 cursor-pointer"
              >
                Entendido
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
