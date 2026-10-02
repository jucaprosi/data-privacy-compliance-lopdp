"use client";

import React from "react";
import { SlidersHorizontal } from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import {
  PERFIL_VACIO,
  SELECTORES_PERFIL,
  avisoCoherenciaDpd,
  respuestasPendientes,
  type ClavePerfil,
  type RespuestaPerfil,
} from "@/lib/bancoPreguntas";

interface PerfilOperacionFormProps {
  /** Resalta en rojo las preguntas sin responder (tras un intento de continuar). */
  resaltarPendientes?: boolean;
  className?: string;
}

/**
 * Preguntas del perfil de operación. Todas son obligatorias: mientras alguna
 * quede sin responder, el diagnóstico no avanza.
 */
export default function PerfilOperacionForm({ resaltarPendientes = false, className = "" }: PerfilOperacionFormProps) {
  const companyData = useAuditStore((s) => s.companyData);
  const setCompanyData = useAuditStore((s) => s.setCompanyData);

  const perfil = companyData.perfil ?? PERFIL_VACIO;
  const pendientes = respuestasPendientes(companyData.perfil);
  const avisoDpd = avisoCoherenciaDpd(companyData.perfil, companyData.sector);

  const responder = (clave: ClavePerfil, valor: RespuestaPerfil) =>
    setCompanyData({ perfil: { ...perfil, [clave]: valor } });

  return (
    <div
      className={`bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-xl p-5 shadow-sm space-y-3 ${className}`}
    >
      <div className="border-b border-zinc-200 dark:border-[#26262b] pb-2.5">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-900 dark:text-white flex items-center">
          <SlidersHorizontal className="w-4 h-4 mr-1.5 text-[#9a3bf1]" />
          Perfil de Operación <span className="text-[#ff1744] ml-1">*</span>
        </h3>
        <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">
          Responda Sí o No a todas las preguntas: son obligatorias y no se puede continuar con alguna sin responder. Si
          no está seguro, consulte con el área correspondiente antes de contestar: sus respuestas definen qué
          controles se evaluarán.
        </p>
      </div>

      <div className="border border-zinc-200 dark:border-[#26262b] rounded-lg overflow-hidden text-xs">
        {SELECTORES_PERFIL.map((sel, i) => {
          const sinResponder = perfil[sel.clave] === null || perfil[sel.clave] === undefined;
          const marcar = resaltarPendientes && sinResponder;
          return (
            <div
              key={sel.clave}
              data-pendiente={sinResponder ? "true" : "false"}
              className={`flex flex-col sm:flex-row sm:items-center gap-2 px-3.5 py-2.5 border-l-4 ${
                marcar ? "border-l-[#ff1744] bg-[#ff1744]/5" : "border-l-transparent"
              } ${!marcar ? (i % 2 === 0 ? "bg-zinc-50 dark:bg-[#0a0a0c]" : "bg-white dark:bg-[#141417]") : ""}`}
            >
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-zinc-800 dark:text-zinc-200" id={`perfil-${sel.clave}`}>
                  {sel.pregunta}
                </p>
                <p className="text-[10px] text-zinc-500 dark:text-zinc-400 mt-0.5">{sel.ayuda}</p>
                {marcar && (
                  <p role="alert" className="text-[10px] font-semibold text-[#ff1744] mt-0.5">
                    Responda esta pregunta para continuar.
                  </p>
                )}
              </div>
              <div
                role="radiogroup"
                aria-labelledby={`perfil-${sel.clave}`}
                aria-required="true"
                className="flex items-center gap-5 shrink-0"
              >
                {(["si", "no"] as const).map((valor) => (
                  <label key={valor} className="flex items-center gap-1.5 cursor-pointer text-zinc-700 dark:text-zinc-300">
                    <input
                      type="radio"
                      name={`perfil-${sel.clave}`}
                      checked={perfil[sel.clave] === valor}
                      onChange={() => responder(sel.clave, valor)}
                      className="accent-[#9a3bf1]"
                    />
                    {valor === "si" ? "Sí" : "No"}
                  </label>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {avisoDpd && (
        <p role="alert" className="text-[11px] text-[#ffab00] bg-[#ffab00]/10 border border-[#ffab00]/30 rounded-lg px-3 py-2">
          {avisoDpd}
        </p>
      )}

      <p className={`text-[11px] ${pendientes === 0 ? "text-[#00c853]" : "text-zinc-500 dark:text-zinc-400"}`}>
        {pendientes === 0
          ? "Perfil completo."
          : `Faltan ${pendientes} pregunta(s) por responder. No podrá continuar hasta completarlas todas.`}
      </p>
    </div>
  );
}
