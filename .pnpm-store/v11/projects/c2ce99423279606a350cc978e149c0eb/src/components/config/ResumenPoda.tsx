"use client";

import React, { useMemo, useState } from "react";
import { ChevronDown, Filter, Info, Lock, MinusCircle } from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { normalizarTamano } from "@/lib/bancoPreguntas";
import { resumenPoda } from "@/lib/bancoPreguntas/resumenPoda";

export default function ResumenPoda() {
  const tamanoFicha = useAuditStore((s) => s.companyData.tamano);
  const perfil = useAuditStore((s) => s.companyData.perfil);
  const talla = normalizarTamano(tamanoFicha);
  const resumen = useMemo(() => resumenPoda(talla, undefined, perfil), [talla, perfil]);
  const [verOmitidos, setVerOmitidos] = useState(false);

  const porcentaje = resumen.totalBanco > 0 ? (resumen.aplicables / resumen.totalBanco) * 100 : 0;

  return (
    <div className="bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-xl p-5 shadow-sm space-y-4">
      <div className="border-b border-zinc-200 dark:border-[#26262b] pb-2.5">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-900 dark:text-white flex items-center">
          <Filter className="w-4 h-4 mr-1.5 text-[#9a3bf1]" />
          Alcance del Cuestionario por Tamaño y Perfil de Operación
        </h3>
        <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">
          Se actualiza automáticamente al cambiar el tamaño o el perfil de operación en la ficha organizacional.
        </p>
      </div>

      <div className="rounded-lg bg-zinc-50 dark:bg-[#0a0a0c] border border-zinc-200 dark:border-[#26262b] p-4 space-y-2.5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <p className="text-sm font-semibold text-zinc-900 dark:text-white">
            {resumen.tamano.etiqueta}{" "}
            <span className="text-zinc-500 dark:text-zinc-400 font-normal">({resumen.tamano.rangoEmpleados})</span>
            {": "}
            <span className="font-mono text-[#9a3bf1]">{resumen.aplicables}</span>
            <span className="text-zinc-500 dark:text-zinc-400 font-normal"> de </span>
            <span className="font-mono">{resumen.totalBanco}</span>
            <span className="font-normal"> controles exigibles</span>
          </p>
          {resumen.omitidos > 0 && (
            <span className="text-[11px] font-mono text-[#ffab00]">{resumen.omitidos} no exigibles</span>
          )}
        </div>
        <div className="h-2 w-full rounded-full bg-zinc-200 dark:bg-[#26262b] overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{ width: `${porcentaje}%`, background: "linear-gradient(90deg, #9a3bf1, #3892f3)" }}
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <h4 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          Controles exigibles por dimensión
        </h4>
        <div className="divide-y divide-zinc-200 dark:divide-[#26262b] border border-zinc-200 dark:border-[#26262b] rounded-lg overflow-hidden bg-white dark:bg-[#0a0a0c]">
          {resumen.porDimension.map((d) => {
            const completa = d.aplicables === d.total;
            return (
              <div key={d.id} className="px-3.5 py-2 flex items-center gap-3 text-xs">
                <span className="font-mono text-[10px] text-zinc-500 w-7 shrink-0">{d.id}</span>
                <span className="flex-1 min-w-0 truncate text-zinc-800 dark:text-zinc-200" title={d.nombre}>
                  {d.nombre}
                </span>
                <div className="hidden sm:block w-28 h-1.5 rounded-full bg-zinc-200 dark:bg-[#26262b] overflow-hidden shrink-0">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${d.total > 0 ? (d.aplicables / d.total) * 100 : 0}%`,
                      background: completa ? "#00c853" : "#3892f3",
                    }}
                  />
                </div>
                <span className="font-mono text-[11px] w-12 text-right shrink-0 text-zinc-700 dark:text-zinc-300">
                  {d.aplicables}/{d.total}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="space-y-1.5">
        <h4 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          Controles estructurales ({resumen.estructurales.length})
        </h4>
        <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
          {resumen.estructuralesSiempreAplican
            ? "Se exigen a cualquier tamaño de organización: sin ellos el resto del sistema no puede demostrarse."
            : "Controles habilitadores: sin ellos el resto del sistema no puede demostrarse."}
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {resumen.estructurales.map((c) => (
            <div
              key={c.id}
              className="flex items-start gap-2 p-2.5 rounded-lg border border-[#00c853]/30 bg-[#00c853]/5 text-xs"
            >
              <Lock className="w-3.5 h-3.5 text-[#00c853] shrink-0 mt-0.5" />
              <div className="min-w-0">
                <p className="font-medium text-zinc-900 dark:text-zinc-100">
                  <span className="font-mono text-[10px] text-zinc-500 mr-1">#{c.id}</span>
                  {c.control}
                </p>
                <p className="text-[10px] text-zinc-500 dark:text-zinc-400 truncate">{c.dimensionNombre}</p>
              </div>
              <span className={`ml-auto text-[10px] font-bold shrink-0 ${c.aplica ? "text-[#00c853]" : "text-[#ffab00]"}`}>
                {c.aplica ? "Siempre exigible" : "No exigible"}
              </span>
            </div>
          ))}
        </div>
      </div>

      {resumen.omitidos > 0 ? (
        <div className="border border-zinc-200 dark:border-[#26262b] rounded-lg overflow-hidden">
          <button
            type="button"
            onClick={() => setVerOmitidos((v) => !v)}
            aria-expanded={verOmitidos}
            className="w-full px-3.5 py-2.5 flex items-center justify-between text-xs font-semibold text-zinc-800 dark:text-zinc-200 bg-zinc-50 dark:bg-[#0a0a0c] hover:bg-zinc-100 dark:hover:bg-[#1e1e24] transition cursor-pointer"
          >
            <span className="flex items-center">
              <MinusCircle className="w-3.5 h-3.5 mr-1.5 text-[#ffab00]" />
              Controles no exigibles según tamaño y perfil ({resumen.omitidos})
            </span>
            <ChevronDown className={`w-4 h-4 transition-transform ${verOmitidos ? "rotate-180" : ""}`} />
          </button>
          {verOmitidos && (
            <div className="border-t border-zinc-200 dark:border-[#26262b]">
              <div className="flex items-start gap-2 p-3 text-[11px] leading-relaxed text-zinc-600 dark:text-zinc-400 bg-[#ffab00]/5">
                <Info className="w-3.5 h-3.5 text-[#ffab00] shrink-0 mt-0.5" />
                <span>
                  Estos controles presuponen una estructura que no es esperable en una organización de este tamaño
                  (comités, áreas especializadas, programas formales) o una actividad que su perfil de operación
                  indica que no realiza. Preguntarlos generaría una brecha artificial que distorsiona el resultado
                  sin reflejar un incumplimiento real. Se incorporan automáticamente si cambia el tamaño o el perfil.
                </span>
              </div>
              <div className="divide-y divide-zinc-200 dark:divide-[#26262b] max-h-72 overflow-y-auto bg-white dark:bg-[#0a0a0c]">
                {resumen.controlesOmitidos.map((c) => (
                  <div key={c.id} className="px-3.5 py-2 flex items-center gap-3 text-xs">
                    <span className="font-mono text-[10px] text-zinc-500 w-7 shrink-0">#{c.id}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-zinc-800 dark:text-zinc-200 truncate" title={c.control}>
                        {c.control}
                      </p>
                      <p className="text-[10px] text-zinc-500 dark:text-zinc-400 truncate">{c.dimensionNombre}</p>
                    </div>
                    <span className="text-[10px] text-zinc-500 dark:text-zinc-400 shrink-0 text-right max-w-[45%]">
                      {c.motivoPerfil ? (
                        <>No aplica: <strong className="text-zinc-700 dark:text-zinc-300">{c.motivoPerfil}</strong></>
                      ) : (
                        <>
                          Aplica desde{" "}
                          <strong className="text-zinc-700 dark:text-zinc-300">{c.tamanoMinimo.etiqueta}</strong>
                        </>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-2 text-zinc-500 text-xs italic">
          Todos los controles del banco son exigibles para esta talla.
        </div>
      )}
    </div>
  );
}
