// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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
      className={`bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-5 shadow-sm space-y-3 ${className}`}
    >
      <div className="border-b border-[var(--ui-borde)] pb-2.5">
        <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--foreground)] flex items-center">
          <SlidersHorizontal className="w-4 h-4 mr-1.5 text-[var(--ui-enlace)]" />
          Perfil de Operación <span className="text-[var(--ui-error-texto)] ml-1">*</span>
        </h3>
        <p className="text-[11px] text-[var(--ui-texto-suave)] mt-0.5">
          Responda Sí o No a todas las preguntas: son obligatorias y no se puede continuar con alguna sin responder. Si
          no está seguro, consulte con el área correspondiente antes de contestar: sus respuestas definen qué
          controles se evaluarán.
        </p>
      </div>

      <div className="border border-[var(--ui-borde)] rounded-lg overflow-hidden text-xs">
        {SELECTORES_PERFIL.map((sel, i) => {
          const sinResponder = perfil[sel.clave] === null || perfil[sel.clave] === undefined;
          const marcar = resaltarPendientes && sinResponder;
          return (
            <div
              key={sel.clave}
              data-pendiente={sinResponder ? "true" : "false"}
              className={`flex flex-col sm:flex-row sm:items-center gap-2 px-3.5 py-2.5 border-l-4 ${
                marcar ? "border-l-[var(--ui-error-borde)] bg-[var(--ui-error-fondo)]" : "border-l-transparent"
              } ${!marcar ? (i % 2 === 0 ? "bg-[var(--ui-superficie-2)]" : "bg-[var(--ui-superficie)]") : ""}`}
            >
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-[var(--foreground)]" id={`perfil-${sel.clave}`}>
                  {sel.pregunta}
                </p>
                <p className="text-[10px] text-[var(--ui-texto-suave)] mt-0.5">{sel.ayuda}</p>
                {marcar && (
                  <p role="alert" className="text-[10px] font-semibold text-[var(--ui-error-texto)] mt-0.5">
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
                  <label key={valor} className="flex items-center gap-1.5 cursor-pointer text-[var(--foreground)]">
                    <input
                      type="radio"
                      name={`perfil-${sel.clave}`}
                      checked={perfil[sel.clave] === valor}
                      onChange={() => responder(sel.clave, valor)}
                      className="accent-[var(--ui-primario)]"
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
        <p role="alert" className="text-[11px] text-[var(--ui-aviso-texto)] bg-[var(--ui-aviso-fondo)] border border-[var(--ui-aviso-borde)] rounded-lg px-3 py-2">
          {avisoDpd}
        </p>
      )}

      <p className={`text-[11px] ${pendientes === 0 ? "text-[var(--ui-exito-texto)]" : "text-[var(--ui-texto-suave)]"}`}>
        {pendientes === 0
          ? "Perfil completo."
          : `Faltan ${pendientes} pregunta(s) por responder. No podrá continuar hasta completarlas todas.`}
      </p>
    </div>
  );
}
