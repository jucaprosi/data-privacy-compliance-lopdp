"use client";

import React, { useState } from "react";
import { etiquetaEstadoCumplimiento } from "@/lib/estadosCumplimiento";
import { AlertTriangle, Check, Pencil, Quote, Sparkles, X } from "lucide-react";
import type { DecisionPropuesta, EstadoPropuesta, PropuestaIA } from "@/lib/preanalisis/tipos";

interface TarjetaPropuestaProps {
  propuesta: PropuestaIA;
  /** Estado que el auditor ya tiene marcado en el control, si lo hay. */
  respuestaActual?: string;
  onAceptar: () => void;
  onEditar: () => void;
  onDescartar: () => void;
}

const COLOR_ESTADO: Record<EstadoPropuesta, string> = {
  Conforme: "bg-[#00c853]/10 text-[#00c853] border-[#00c853]/40",
  Parcial: "bg-[#ffab00]/10 text-[#ffab00] border-[#ffab00]/40",
  "Sin sustento": "bg-[#26262b] text-zinc-300 border-[#3a3a42]",
};

const ETIQUETA_DECISION: Record<Exclude<DecisionPropuesta, "pendiente">, string> = {
  aceptada: "Propuesta aceptada por el auditor",
  editada: "Propuesta editada por el auditor",
  descartada: "Propuesta descartada por el auditor",
};

export default function TarjetaPropuesta({
  propuesta,
  respuestaActual,
  onAceptar,
  onEditar,
  onDescartar,
}: TarjetaPropuestaProps) {
  const sinSustento = propuesta.estado === "Sin sustento";
  const [confirmando, setConfirmando] = useState<"aceptada" | "editada" | null>(null);

  // Aplicar la propuesta cambiaría una respuesta que el auditor ya dio: se pide
  // confirmación explícita antes de reemplazarla.
  const reemplazaRespuesta =
    Boolean(respuestaActual) &&
    respuestaActual !== "Pendiente" &&
    respuestaActual !== propuesta.estado;

  const solicitar = (modo: "aceptada" | "editada") => {
    if (reemplazaRespuesta) {
      setConfirmando(modo);
      return;
    }
    if (modo === "aceptada") onAceptar();
    else onEditar();
  };

  const confirmar = () => {
    if (confirmando === "aceptada") onAceptar();
    else if (confirmando === "editada") onEditar();
    setConfirmando(null);
  };

  return (
    <div className="bg-[#141417] border border-[#26262b] rounded-xl p-4 space-y-3 text-xs text-zinc-300">
      <div className="flex flex-wrap items-center gap-2">
        <Sparkles className="w-4 h-4 text-[#9a3bf1]" />
        <span className="text-[11px] font-bold uppercase tracking-wider text-white">Propuesta de la IA</span>
        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${COLOR_ESTADO[propuesta.estado]}`}>
          {etiquetaEstadoCumplimiento(propuesta.estado)}
        </span>
        <span className="text-[10px] font-mono text-zinc-400">
          {propuesta.nivelEvidenciaMaximo === 1 ? "Sustento máximo E1" : "Sin nivel de evidencia sustentado"}
        </span>
        <span className="ml-auto text-[10px] font-mono text-zinc-500">
          {propuesta.evidenciaCodigo} · {propuesta.modelo}
        </span>
      </div>

      {propuesta.citas.length > 0 && (
        <ul className="space-y-1.5">
          {propuesta.citas.map((cita, indice) => (
            <li key={indice} className="p-2.5 rounded-lg bg-[#0a0a0c] border border-[#26262b] space-y-1">
              <div className="flex items-center gap-1 text-[10px] font-semibold text-[#3892f3]">
                <Quote className="w-3 h-3" />
                Citada literalmente del documento
              </div>
              <p className="text-[11px] text-zinc-200 whitespace-pre-wrap break-words leading-relaxed">
                {cita.fragmento}
              </p>
              {cita.motivo && <p className="text-[11px] text-zinc-500 leading-relaxed">{cita.motivo}</p>}
            </li>
          ))}
        </ul>
      )}

      {propuesta.citasDescartadas > 0 && (
        <div className="flex items-start gap-2 p-2 rounded-lg bg-[#ffab00]/10 border border-[#ffab00]/30 text-[11px] text-[#ffab00]">
          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>
            {propuesta.citasDescartadas} cita(s) del modelo no se encontraron en el documento y se descartaron.
          </span>
        </div>
      )}

      <div>
        <div className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 mb-0.5">Razonamiento</div>
        <p className="text-[11px] leading-relaxed whitespace-pre-wrap break-words">{propuesta.razonamiento}</p>
      </div>

      {propuesta.limitaciones.length > 0 && (
        <div>
          <div className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 mb-0.5">Limitaciones</div>
          <ul className="list-disc pl-4 space-y-0.5 text-[11px] text-zinc-400">
            {propuesta.limitaciones.map((limitacion, indice) => (
              <li key={indice}>{limitacion}</li>
            ))}
          </ul>
        </div>
      )}

      {propuesta.decision === "pendiente" ? (
        <div className="space-y-1.5 pt-2 border-t border-[#26262b]">
          {sinSustento && (
            <p className="text-[11px] text-[#ffab00]">
              El documento no sustenta este control: respóndelo manualmente
            </p>
          )}
          {confirmando && (
            <div
              role="alertdialog"
              className="p-2.5 rounded-lg bg-[#ffab00]/10 border border-[#ffab00]/40 space-y-2"
            >
              <p className="text-[11px] text-[#ffab00] leading-relaxed">
                Ya respondiste «{etiquetaEstadoCumplimiento(respuestaActual ?? "")}» en este control. Aplicar la propuesta lo
                reemplazará por «{etiquetaEstadoCumplimiento(propuesta.estado)}».
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={confirmar}
                  className="px-2.5 py-1 rounded-md bg-[#ffab00] text-black text-[11px] font-semibold cursor-pointer"
                >
                  Reemplazar mi respuesta
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmando(null)}
                  className="px-2.5 py-1 rounded-md border border-[#26262b] text-zinc-300 text-[11px] cursor-pointer"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => solicitar("aceptada")}
              disabled={sinSustento}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-[#00c853] text-black text-xs font-semibold hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
              <Check className="w-3.5 h-3.5" />
              Aceptar propuesta
            </button>
            <button
              type="button"
              onClick={() => solicitar("editada")}
              disabled={sinSustento}
              title="Aplica la propuesta como punto de partida para que la ajustes tú"
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md border border-[#3892f3]/50 text-[#3892f3] text-xs font-semibold hover:bg-[#3892f3]/10 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
              <Pencil className="w-3.5 h-3.5" />
              Aplicar y ajustar
            </button>
            <button
              type="button"
              onClick={onDescartar}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md border border-[#26262b] text-zinc-300 text-xs hover:bg-[#1e1e24] cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
              Descartar
            </button>
          </div>
        </div>
      ) : (
        <div className="pt-2 border-t border-[#26262b] text-[11px] font-semibold text-zinc-300">
          {ETIQUETA_DECISION[propuesta.decision]}
        </div>
      )}
    </div>
  );
}
