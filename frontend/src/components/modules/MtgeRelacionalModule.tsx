"use client";

import React, { useState, useTransition } from "react";
import {
  GitBranch,
  Play,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ShieldAlert,
  Users,
  Activity,
  Database,
  Info,
} from "lucide-react";
import type { ResultadoMTGERelacional } from "@/app/actions/mtgeActions";
import { evaluarNecesidadEIPD } from "@/app/actions/mtgeActions";

// ---------------------------------------------------------------------------
// Helpers visuales
// ---------------------------------------------------------------------------

const CRITERIO_META: Record<
  ResultadoMTGERelacional["criterioActivacion"],
  { label: string; color: string; icon: React.ReactNode }
> = {
  CRITERIO_A_VOLUMEN_MASIVO: {
    label: "Criterio A — Volumen Masivo",
    color: "bg-rose-950 border-rose-800 text-rose-300",
    icon: <Users className="w-3.5 h-3.5 mr-1" />,
  },
  CRITERIO_B_SENSIBLE_LONG_RETENTION: {
    label: "Criterio B — Datos Sensibles · Retención Larga",
    color: "bg-orange-950 border-orange-800 text-orange-300",
    icon: <AlertTriangle className="w-3.5 h-3.5 mr-1" />,
  },
  CRITERIO_A_Y_B: {
    label: "Criterios A + B — Riesgo Máximo",
    color: "bg-red-950 border-red-800 text-red-300",
    icon: <ShieldAlert className="w-3.5 h-3.5 mr-1" />,
  },
  NINGUNO: {
    label: "Sin criterio activado",
    color: "bg-emerald-950 border-emerald-800 text-emerald-300",
    icon: <CheckCircle className="w-3.5 h-3.5 mr-1" />,
  },
};

function formatFecha(iso: string): string {
  try {
    return new Date(iso).toLocaleString("es-EC", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// Componente Principal: MtgeRelacionalModule
// ---------------------------------------------------------------------------

export default function MtgeRelacionalModule() {
  const [resultado, setResultado] = useState<ResultadoMTGERelacional | null>(null);
  const [errorGlobal, setErrorGlobal] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const ejecutarEvaluacion = () => {
    setErrorGlobal(null);
    startTransition(async () => {
      const res = await evaluarNecesidadEIPD();
      if (res.success && res.data) {
        setResultado(res.data);
      } else {
        setErrorGlobal(res.error ?? "Error desconocido en el motor MTGE Relacional.");
      }
    });
  };

  const criterioMeta = resultado
    ? CRITERIO_META[resultado.criterioActivacion]
    : null;

  return (
    <div className="space-y-6">
      {/* Encabezado */}
      <div className="pb-4 border-b border-zinc-800">
        <h2 className="text-xl font-bold text-zinc-100 flex items-center">
          <Activity className="w-5 h-5 mr-2 text-amber-400" />
          Motor MTGE Relacional · Gran Escala
        </h2>
        <p className="text-xs text-zinc-400 mt-1">
          Evaluación normativa del RAT Maestro completo — Res. SPDP-SPD-2026-0005-R Arts. 12-13 ·
          LOPDP Arts. 25, 44, 48 · Invariante: INV_LOPDP_MTGE_DETERMINISTIC_TRIGGER
        </p>
      </div>

      {/* Diferencia con el módulo MTGE paramétrico */}
      <div className="p-3 bg-zinc-900/40 border border-zinc-800 rounded-xl flex items-start space-x-3 text-xs">
        <Info className="w-4 h-4 text-zinc-500 mt-0.5 shrink-0" />
        <div className="text-zinc-400 space-y-1">
          <p>
            <span className="text-zinc-300 font-semibold">Motor Relacional</span> — evalúa el
            RAT Maestro completo del tenant como entidad jurídica única y decide si el conjunto
            total supera umbrales de Gran Escala.
          </p>
          <p>
            <span className="text-zinc-500">Módulo Riesgos &amp; MTGE</span> — calcula el score
            paramétrico por actividad individual.
          </p>
        </div>
      </div>

      {/* Criterios normativos (siempre visibles) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 space-y-2">
          <div className="font-semibold text-zinc-300 flex items-center pb-1 border-b border-zinc-800">
            <Users className="w-3.5 h-3.5 mr-1.5 text-rose-400" />
            Criterio A — Volumen Masivo
          </div>
          <p className="text-zinc-400 leading-relaxed">
            Si la suma de titulares en el RAT Maestro supera los{" "}
            <span className="text-rose-300 font-mono font-bold">10,000</span> registros, se activa
            EIPD forzosa en todas las actividades afectadas. El flag{" "}
            <code className="text-amber-300">requiereEIPD = true</code> se persiste de forma
            irreversible.
          </p>
          <div className="text-zinc-600">
            Res. SPDP-SPD-2026-0005-R Art. 12
          </div>
        </div>

        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 space-y-2">
          <div className="font-semibold text-zinc-300 flex items-center pb-1 border-b border-zinc-800">
            <AlertTriangle className="w-3.5 h-3.5 mr-1.5 text-orange-400" />
            Criterio B — Sensible + Retención &gt; 3 años
          </div>
          <p className="text-zinc-400 leading-relaxed">
            Si existe al menos una actividad con datos{" "}
            <span className="text-orange-300 font-semibold">Biométricos o de Salud</span> (Art.
            25 LOPDP) con retención superior a{" "}
            <span className="text-orange-300 font-mono font-bold">3 años</span>, activa EIPD
            previa obligatoria (Art. 44 LOPDP).
          </p>
          <div className="text-zinc-600">
            Res. SPDP-SPD-2026-0005-R Art. 13
          </div>
        </div>
      </div>

      {/* Botón de evaluación */}
      <div className="flex items-center justify-between">
        <div className="text-xs text-zinc-500">
          {resultado
            ? `Última evaluación: ${formatFecha(resultado.evaluadoEn)}`
            : "Sin evaluación ejecutada en esta sesión."}
        </div>
        <button
          type="button"
          onClick={ejecutarEvaluacion}
          disabled={isPending}
          className={`flex items-center space-x-2 px-5 py-2.5 font-bold rounded-xl text-sm transition cursor-pointer disabled:opacity-50 shadow-lg ${
            resultado?.requiereEIPDForzoso
              ? "bg-rose-700 hover:bg-rose-600 shadow-rose-950 text-white"
              : "bg-amber-600 hover:bg-amber-500 shadow-amber-950 text-white"
          }`}
        >
          <Play className="w-4 h-4" />
          <span>
            {isPending ? "Evaluando RAT Maestro..." : "Ejecutar Evaluación MTGE Relacional"}
          </span>
        </button>
      </div>

      {/* Error global */}
      {errorGlobal && (
        <div className="p-4 bg-rose-950/20 border border-rose-800/40 rounded-xl flex items-start space-x-3 text-rose-400 text-sm">
          <XCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Error en la evaluación</p>
            <p className="text-xs mt-1 text-rose-400/80">{errorGlobal}</p>
          </div>
        </div>
      )}

      {/* Esqueleto animado mientras carga */}
      {isPending && !resultado && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-16 bg-zinc-800/40 animate-pulse rounded-xl border border-zinc-800"
            />
          ))}
        </div>
      )}

      {/* Resultado del Motor */}
      {resultado && !isPending && (
        <div className="space-y-4">
          {/* Veredicto principal */}
          <div
            className={`p-5 rounded-2xl border ${
              resultado.requiereEIPDForzoso
                ? "bg-rose-950/20 border-rose-800/60"
                : "bg-emerald-950/20 border-emerald-800/60"
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                {resultado.requiereEIPDForzoso ? (
                  <ShieldAlert className="w-7 h-7 text-rose-400" />
                ) : (
                  <CheckCircle className="w-7 h-7 text-emerald-400" />
                )}
                <div>
                  <h3
                    className={`font-bold text-lg ${
                      resultado.requiereEIPDForzoso
                        ? "text-rose-300"
                        : "text-emerald-300"
                    }`}
                  >
                    {resultado.requiereEIPDForzoso
                      ? "EIPD FORZOSA ACTIVADA"
                      : "Sin obligación de EIPD"}
                  </h3>
                  <p className="text-xs text-zinc-500 mt-0.5">
                    Motor MTGE Relacional · Res. SPDP-SPD-2026-0005-R
                  </p>
                </div>
              </div>

              {/* Badge criterio */}
              {criterioMeta && (
                <span
                  className={`flex items-center px-3 py-1.5 rounded-lg border text-xs font-bold ${criterioMeta.color}`}
                >
                  {criterioMeta.icon}
                  {criterioMeta.label}
                </span>
              )}
            </div>

            {/* Rationale */}
            <p className="text-xs text-zinc-300 leading-relaxed italic bg-zinc-950/40 p-3 rounded-lg border border-zinc-800/60">
              {resultado.rationale}
            </p>
          </div>

          {/* Métricas detalladas */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            {/* Volumen total */}
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 text-center">
              <Database className="w-5 h-5 mx-auto mb-2 text-zinc-500" />
              <div
                className={`text-3xl font-bold font-mono ${
                  resultado.superaUmbralVolumen ? "text-rose-400" : "text-zinc-300"
                }`}
              >
                {resultado.volumenTotalTitulares.toLocaleString("es-EC")}
              </div>
              <div className="text-zinc-500 mt-1 text-[10px] uppercase tracking-wide">
                Titulares totales en RAT
              </div>
              <div
                className={`mt-2 px-2 py-0.5 rounded text-[10px] font-bold inline-flex items-center border ${
                  resultado.superaUmbralVolumen
                    ? "bg-rose-950 text-rose-300 border-rose-800"
                    : "bg-zinc-800 text-zinc-400 border-zinc-700"
                }`}
              >
                {resultado.superaUmbralVolumen ? "Supera umbral 10K" : "Bajo umbral 10K"}
              </div>
            </div>

            {/* Tratamientos sensibles */}
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 text-center">
              <AlertTriangle className="w-5 h-5 mx-auto mb-2 text-zinc-500" />
              <div
                className={`text-3xl font-bold font-mono ${
                  resultado.tieneTratamientoSensibleLargo ? "text-orange-400" : "text-zinc-300"
                }`}
              >
                {resultado.tieneTratamientoSensibleLargo ? "SÍ" : "NO"}
              </div>
              <div className="text-zinc-500 mt-1 text-[10px] uppercase tracking-wide">
                Sensibles &gt; 3 años
              </div>
              <div
                className={`mt-2 px-2 py-0.5 rounded text-[10px] font-bold inline-flex items-center border ${
                  resultado.tieneTratamientoSensibleLargo
                    ? "bg-orange-950 text-orange-300 border-orange-800"
                    : "bg-zinc-800 text-zinc-400 border-zinc-700"
                }`}
              >
                {resultado.tieneTratamientoSensibleLargo
                  ? "Criterio B activo"
                  : "Criterio B inactivo"}
              </div>
            </div>

            {/* Actividades que detonan */}
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 text-center">
              <GitBranch className="w-5 h-5 mx-auto mb-2 text-zinc-500" />
              <div
                className={`text-3xl font-bold font-mono ${
                  resultado.actividadesQueDetonan.length > 0
                    ? "text-amber-400"
                    : "text-zinc-300"
                }`}
              >
                {resultado.actividadesQueDetonan.length}
              </div>
              <div className="text-zinc-500 mt-1 text-[10px] uppercase tracking-wide">
                Actividades detonantes
              </div>
              {resultado.actividadesQueDetonan.length > 0 && (
                <div className="mt-2 text-[10px] text-zinc-500 font-mono">
                  {resultado.actividadesQueDetonan.slice(0, 2).join(", ")}
                  {resultado.actividadesQueDetonan.length > 2 && (
                    <span> +{resultado.actividadesQueDetonan.length - 2} más</span>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Aviso de mutación permanente */}
          {resultado.requiereEIPDForzoso && (
            <div className="p-3 bg-amber-950/20 border border-amber-800/40 rounded-xl flex items-start space-x-3 text-xs text-amber-300">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" />
              <p>
                <span className="font-bold">Mutación permanente aplicada:</span> El flag{" "}
                <code>requiereEIPD = true</code> ha sido escrito de forma irreversible en el
                RAT Maestro. No puede revertirse sin aprobación del DPO (Art. 48 LOPDP — SoD).
              </p>
            </div>
          )}
        </div>
      )}

      {/* Leyenda normativa */}
      <div className="text-[10px] text-zinc-600 border-t border-zinc-800 pt-3 flex items-center space-x-2">
        <Activity className="w-3 h-3 text-zinc-700" />
        <span>
          Motor determinista · Criterio A: 10,000 titulares · Criterio B: Biom/Salud &gt; 3 años ·
          Res. SPDP-SPD-2026-0005-R Arts. 12-13 · LOPDP Arts. 25, 44, 48
        </span>
      </div>
    </div>
  );
}
