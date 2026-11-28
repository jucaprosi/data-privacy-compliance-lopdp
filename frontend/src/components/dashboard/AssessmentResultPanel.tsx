// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

import React from "react";
import AssessmentExecutiveSummary from "./AssessmentExecutiveSummary";
import dimensionStyles from "@/components/DimensionIdentity.module.css";
import { ordenarDimensionesPorPrioridad } from "@/lib/assessmentPriorities";
import {
  XCircle,
  CheckCircle2,
  Layers,
  ClipboardList,
  Target,
  FileWarning,
  BadgeCheck,
} from "lucide-react";
import {
  CONTROLES_ESTRUCTURALES,
  type ControlEstructural,
} from "@/lib/dimensionesSGPDP";
import {
  useAuditStore,
  type BrechaDetectada,
  type ResultadoDimension,
} from "@/store/useAuditStore";


interface TonoSemantico {
  texto: string;
  fondo: string;
  borde: string;
}

const TONO_CRITICO: TonoSemantico = {
  texto: "text-[var(--ui-error-texto)]",
  fondo: "bg-[var(--ui-error-fondo)]",
  borde: "border-[var(--ui-error-borde)]",
};

const TONO_ADVERTENCIA: TonoSemantico = {
  texto: "text-[var(--ui-aviso-texto)]",
  fondo: "bg-[var(--ui-aviso-fondo)]",
  borde: "border-[var(--ui-aviso-borde)]",
};

const TONO_EXITO: TonoSemantico = {
  texto: "text-[var(--ui-exito-texto)]",
  fondo: "bg-[var(--ui-exito-fondo)]",
  borde: "border-[var(--ui-exito-borde)]",
};

const TONO_NEUTRO: TonoSemantico = {
  texto: "text-[var(--foreground)]",
  fondo: "bg-[var(--ui-boton)]",
  borde: "border-[var(--ui-borde)]",
};

/** Umbral de score por debajo del cual una dimensión se marca como deficitaria. */
const UMBRAL_SCORE_DEFICITARIO = 60;

/** Traduce un nivel de madurez (0-5) a su tono semántico de presentación. */
function tonoPorNivel(nivel: number): TonoSemantico {
  if (nivel <= 0) return TONO_NEUTRO;
  if (nivel <= 2) return TONO_CRITICO;
  if (nivel === 3) return TONO_ADVERTENCIA;
  return TONO_EXITO;
}

/** Traduce un score porcentual (0-100) a su tono semántico de presentación. */
function tonoPorScore(score: number): TonoSemantico {
  if (score < 40) return TONO_CRITICO;
  if (score < UMBRAL_SCORE_DEFICITARIO) return TONO_ADVERTENCIA;
  return TONO_EXITO;
}

/** Traduce la severidad de una brecha a su tono semántico de presentación. */
function tonoPorSeveridad(severidad: BrechaDetectada["severidad"]): TonoSemantico {
  if (severidad === "Crítico") return TONO_CRITICO;
  if (severidad === "Alto") return TONO_ADVERTENCIA;
  return TONO_NEUTRO;
}

/** Color plano de la barra de progreso por rango de score. */
function colorBarraPorScore(score: number): string {
  if (score < 40) return "bg-[var(--ui-error-borde)]";
  if (score < UMBRAL_SCORE_DEFICITARIO) return "bg-[var(--ui-aviso-borde)]";
  if (score < 75) return "bg-[var(--ui-info-borde)]";
  return "bg-[var(--ui-exito-borde)]";
}


export default function AssessmentResultPanel({ onShowTasks }: { onShowTasks: () => void }) {
  const { calcularResultadoAssessment, evidencias } = useAuditStore();
  const resultado = calcularResultadoAssessment("declarado");
  const verificado = calcularResultadoAssessment("verificado");
  const controlesConEvidencia = new Set<number>(
    evidencias.flatMap((e) => e.controlesVinculados)
  );

  if (resultado.totalEvaluados === 0) {
    return (
      <div className="p-8 rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] shadow-xs">
        <div className="max-w-md mx-auto text-center space-y-3">
          <div className="w-12 h-12 rounded-xl bg-[var(--ui-boton)] border border-[var(--ui-borde)] mx-auto flex items-center justify-center text-[var(--ui-texto-suave)]">
            <ClipboardList className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-white tracking-tight">
            Sin Evaluación Registrada
          </h3>
          <p className="text-[11px] text-[var(--ui-texto-suave)] leading-relaxed">
            El motor de madurez SGPDP no dispone todavía de controles evaluados.
            La matriz de dimensiones, los controles estructurales y el registro de
            brechas se materializan al registrar la primera valoración.
          </p>
          <p className="text-[10px] font-mono text-[var(--ui-texto-suave)] pt-1">
            {resultado.totalAplicables} controles aplicables en el alcance podado
          </p>
        </div>
      </div>
    );
  }

  const brechasCriticasLista: BrechaDetectada[] = resultado.brechas.filter(
    (b) => b.severidad === "Crítico"
  );
  const brechasNoCriticas: BrechaDetectada[] = resultado.brechas.filter(
    (b) => b.severidad !== "Crítico"
  );
  const brechasOrdenadas: BrechaDetectada[] = [
    ...brechasCriticasLista,
    ...brechasNoCriticas,
  ];

  /** Identificadores de pregunta con brecha estructural declarada por el motor. */
  const estructuralesDegradados = new Set<number>(
    resultado.brechas.filter((b) => b.esEstructural).map((b) => b.preguntaId)
  );

  return (
    <div className="space-y-4 font-sans">
      <AssessmentExecutiveSummary resultado={resultado} verificado={verificado} onShowTasks={onShowTasks} />

      <div id="assessment-areas" className="rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] shadow-xs overflow-hidden">
        <div className="px-5 py-3 border-b border-[var(--ui-borde)] flex items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-[var(--ui-enlace)]" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Tu avance por área
            </h3>
          </div>
          <span className="text-[11px] font-mono text-[var(--ui-texto-suave)] shrink-0">
            {resultado.dimensiones.length} dimensiones · peso total 1.00
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] border-collapse">
            <thead>
              <tr className="bg-[var(--ui-campo)]/60 border-b border-[var(--ui-borde)]">
                <th className="text-left px-4 py-2.5 text-[10px] font-mono uppercase font-bold text-[var(--ui-texto-suave)] tracking-wider">
                  Dimensión
                </th>
                <th className="text-right px-3 py-2.5 text-[10px] font-mono uppercase font-bold text-[var(--ui-texto-suave)] tracking-wider w-16">
                  Peso
                </th>
                <th className="text-left px-3 py-2.5 text-[10px] font-mono uppercase font-bold text-[var(--ui-texto-suave)] tracking-wider w-44">
                  Score
                </th>
                <th className="text-left px-3 py-2.5 text-[10px] font-mono uppercase font-bold text-[var(--ui-texto-suave)] tracking-wider w-44">
                  Nivel
                </th>
                <th className="text-center px-3 py-2.5 text-[10px] font-mono uppercase font-bold text-[var(--ui-texto-suave)] tracking-wider w-24">
                  Brechas
                </th>
                <th className="text-left px-4 py-2.5 text-[10px] font-mono uppercase font-bold text-[var(--ui-texto-suave)] tracking-wider">
                  Observación
                </th>
              </tr>
            </thead>
            <tbody>
              {ordenarDimensionesPorPrioridad(resultado.dimensiones, verificado.brechas).map((dim: ResultadoDimension) => {
                const deficitaria =
                  dim.brechasCriticas > 0 ||
                  (dim.itemsEvaluados > 0 && dim.score < UMBRAL_SCORE_DEFICITARIO);
                const tonoDim = tonoPorNivel(dim.nivel);
                const noEvaluada = dim.itemsEvaluados === 0;

                return (
                  <tr
                    key={dim.id}
                    className={`border-b border-[var(--ui-borde)]/70 last:border-b-0 transition hover:bg-[var(--ui-boton)]/60 ${
                      dim.brechasCriticas > 0
                        ? "bg-[var(--ui-error-fondo)]"
                        : deficitaria
                        ? "bg-[var(--ui-aviso-fondo)]"
                        : ""
                    }`}
                  >
                    {/* Dimensión */}
                    <td className="px-4 py-3 align-top">
                      <div className="flex items-start space-x-2">
                        <span data-dimension={dim.id} className={`${dimensionStyles.identity} ${dimensionStyles.dimensionBadge} text-[10px] font-mono px-1.5 py-0.5 rounded border shrink-0 mt-0.5`}>
                          {dim.id}
                        </span>
                        <div className="min-w-0">
                          <p className="text-[11px] font-semibold text-white leading-snug">
                            {dim.nombre}
                          </p>
                          <p className="text-[10px] font-mono text-[var(--ui-texto-suave)] mt-0.5">
                            {dim.itemsEvaluados}/{dim.itemsAplicables} evaluados ·{" "}
                            {dim.coberturaPorcentaje.toFixed(0)}% cobertura
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* Peso */}
                    <td className="px-3 py-3 align-top text-right">
                      <span className="text-[11px] font-mono text-white">
                        {dim.peso.toFixed(2)}
                      </span>
                    </td>

                    {/* Score con barra de progreso proporcional */}
                    <td className="px-3 py-3 align-top">
                      <div className="space-y-1.5">
                        <span
                          className={`text-[11px] font-mono font-bold ${
                            noEvaluada ? "text-[var(--ui-texto-suave)]" : tonoPorScore(dim.score).texto
                          }`}
                        >
                          {noEvaluada ? "—" : `${dim.score.toFixed(1)}%`}
                        </span>
                        <div className="w-full h-1.5 rounded-full bg-[var(--ui-campo)] border border-[var(--ui-borde)] overflow-hidden">
                          <div
                            className={`h-full transition-all duration-700 ${colorBarraPorScore(
                              dim.score
                            )}`}
                            style={{
                              width: noEvaluada
                                ? "0%"
                                : `${Math.min(100, Math.max(0, dim.score))}%`,
                            }}
                          />
                        </div>
                      </div>
                    </td>

                    {/* Nivel */}
                    <td className="px-3 py-3 align-top">
                      {noEvaluada || dim.nivel <= 0 ? (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--ui-boton)] text-[var(--ui-texto-suave)] border border-[var(--ui-borde)]">
                          No evaluada
                        </span>
                      ) : (
                        <span
                          className={`inline-flex items-center space-x-1 text-[10px] font-mono px-2 py-0.5 rounded border font-semibold ${tonoDim.fondo} ${tonoDim.texto} ${tonoDim.borde}`}
                        >
                          <span>N{dim.nivel}</span>
                          <span className="font-normal opacity-90">
                            {dim.nivelEtiqueta}
                          </span>
                        </span>
                      )}
                    </td>

                    {/* Conteo de brechas críticas / altas */}
                    <td className="px-3 py-3 align-top">
                      <div className="flex items-center justify-center space-x-1.5 font-mono text-[10px]">
                        <span
                          className={`px-1.5 py-0.5 rounded border ${
                            dim.brechasCriticas > 0
                              ? "bg-[var(--ui-error-fondo)] text-[var(--ui-error-texto)] border-[var(--ui-error-borde)] font-bold"
                              : "bg-[var(--ui-boton)] text-[var(--ui-texto-suave)] border-[var(--ui-borde)]"
                          }`}
                          title="Brechas críticas"
                        >
                          C {dim.brechasCriticas}
                        </span>
                        <span
                          className={`px-1.5 py-0.5 rounded border ${
                            dim.brechasAltas > 0
                              ? "bg-[var(--ui-aviso-fondo)] text-[var(--ui-aviso-texto)] border-[var(--ui-aviso-borde)] font-bold"
                              : "bg-[var(--ui-boton)] text-[var(--ui-texto-suave)] border-[var(--ui-borde)]"
                          }`}
                          title="Brechas altas"
                        >
                          A {dim.brechasAltas}
                        </span>
                      </div>
                    </td>

                    {/* Observación */}
                    <td className="px-4 py-3 align-top">
                      <p className="text-[11px] text-[var(--ui-texto-suave)] leading-relaxed">
                        {dim.observacion || "Sin observaciones registradas."}
                      </p>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div id="assessment-bases" className="rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] shadow-xs overflow-hidden">
        <div className="px-5 py-3 border-b border-[var(--ui-borde)] flex items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Target className="w-4 h-4 text-[var(--ui-enlace)]" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Bases para cuidar los datos
            </h3>
          </div>
          <span
            className={`text-[10px] font-mono px-2 py-0.5 rounded border font-semibold shrink-0 ${
              resultado.controlesEstructuralesDegradados > 0
                ? "bg-[var(--ui-error-fondo)] text-[var(--ui-error-texto)] border-[var(--ui-error-borde)]"
                : "bg-[var(--ui-exito-fondo)] text-[var(--ui-exito-texto)] border-[var(--ui-exito-borde)]"
            }`}
          >
            {resultado.controlesEstructuralesDegradados} de {CONTROLES_ESTRUCTURALES.length} bases por fortalecer
          </span>
        </div>

        <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          {CONTROLES_ESTRUCTURALES.map((control: ControlEstructural) => {
            const enBrecha = estructuralesDegradados.has(control.preguntaId);
            return (
              <div
                key={control.preguntaId}
                className={`p-4 rounded-lg border space-y-2.5 transition ${
                  enBrecha
                    ? "bg-[var(--ui-boton)] border-[var(--ui-error-borde)] shadow-[0_0_15px_rgba(255,23,68,0.10)]"
                    : "bg-[var(--ui-boton)] border-[var(--ui-borde)] hover:border-[var(--ui-borde)]"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start space-x-2 min-w-0">
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--ui-campo)] text-[var(--ui-texto-suave)] border border-[var(--ui-borde)] shrink-0 mt-0.5">
                      P{control.preguntaId}
                    </span>
                    <div className="min-w-0">
                      <p className="text-[11px] font-bold text-white leading-snug">
                        {control.nombre}
                      </p>
                      <p className="text-[10px] font-mono text-[var(--ui-texto-suave)] mt-0.5">
                        Dimensión {control.dimension}
                      </p>
                    </div>
                  </div>

                  {enBrecha ? (
                    <span className="flex items-center space-x-1 text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--ui-error-fondo)] text-[var(--ui-error-texto)] border border-[var(--ui-error-borde)] font-semibold shrink-0">
                      <XCircle className="w-3 h-3" />
                      <span>Necesita atención</span>
                    </span>
                  ) : !resultado.controlesEstructuralesEvaluados.includes(control.preguntaId) ? (
                    <span className="flex items-center space-x-1 text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--ui-campo)] text-[var(--ui-texto-suave)] border border-[var(--ui-borde)] font-semibold shrink-0">
                      <span>Sin evaluar</span>
                    </span>
                  ) : (
                    <span className="flex items-center space-x-1 text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--ui-exito-fondo)] text-[var(--ui-exito-texto)] border border-[var(--ui-exito-borde)] font-semibold shrink-0">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>En buen estado</span>
                    </span>
                  )}
                </div>

                <div className="pt-2 border-t border-[var(--ui-borde)]">
                  <span className="text-[10px] font-mono uppercase font-bold text-[var(--ui-texto-suave)] tracking-wider">
                    Tu siguiente paso
                  </span>
                  <p
                    className={`text-[11px] leading-relaxed mt-1 ${
                      enBrecha ? "text-white" : "text-[var(--ui-texto-suave)]"
                    }`}
                  >
                    {control.accionPrioritaria}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] shadow-xs overflow-hidden">
        <div className="px-5 py-3 border-b border-[var(--ui-borde)] flex items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <FileWarning className="w-4 h-4 text-[var(--ui-enlace)]" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Aspectos que necesitan atención
            </h3>
          </div>
          <span className="text-[11px] font-mono text-[var(--ui-texto-suave)] shrink-0">
            {resultado.brechas.length} hallazgo(s) · ordenadas por severidad
          </span>
        </div>

        {resultado.brechas.length === 0 ? (
          <div className="px-5 py-8 text-center space-y-1.5">
            <CheckCircle2 className="w-5 h-5 text-[var(--ui-exito-texto)] mx-auto" />
            <p className="text-[11px] text-[var(--ui-texto-suave)]">
              No se registran brechas sobre los controles evaluados.
            </p>
          </div>
        ) : (
          <div className="max-h-[420px] overflow-y-auto divide-y divide-[var(--ui-borde)]">
            {brechasOrdenadas.map((brecha: BrechaDetectada, indice: number) => {
              const tono = tonoPorSeveridad(brecha.severidad);
              const esCritica = brecha.severidad === "Crítico";
              const primeraNoCritica =
                !esCritica && indice === brechasCriticasLista.length && indice > 0;

              return (
                <div
                  key={`${brecha.preguntaId}-${brecha.dimensionId}`}
                  className={`px-4 py-3 flex items-start gap-3 transition hover:bg-[var(--ui-boton)]/50 ${
                    esCritica ? "bg-[var(--ui-error-fondo)]" : ""
                  } ${primeraNoCritica ? "border-t-2 border-t-[var(--ui-borde)]" : ""}`}
                >
                  {/* Franja de severidad */}
                  <span
                    className={`w-0.5 self-stretch rounded-full shrink-0 ${
                      esCritica
                        ? "bg-[var(--ui-error-borde)]"
                        : brecha.severidad === "Alto"
                        ? "bg-[var(--ui-aviso-borde)]"
                        : "bg-[var(--ui-boton)]"
                    }`}
                  />

                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--ui-boton)] text-[var(--ui-texto-suave)] border border-[var(--ui-borde)] shrink-0 mt-0.5">
                    P{brecha.preguntaId}
                  </span>

                  <div className="min-w-0 flex-1">
                    <p className="text-[11px] font-semibold text-white leading-snug">
                      {brecha.control}
                    </p>
                    <p className="text-[10px] font-mono text-[var(--ui-texto-suave)] mt-0.5 truncate">
                      {brecha.dimensionId} · {brecha.dimensionNombre}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 flex-wrap justify-end">
                    {controlesConEvidencia.has(brecha.preguntaId) ? (
                      <span
                        className="flex items-center text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--ui-exito-fondo)] text-[var(--ui-exito-texto)] border border-[var(--ui-exito-borde)]"
                        title="El control tiene evidencia documental vinculada"
                      >
                        <BadgeCheck className="w-3 h-3 mr-1" />
                        Verificado
                      </span>
                    ) : (
                      <span
                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--ui-campo)] text-[var(--ui-texto-suave)] border border-[var(--ui-borde)]"
                        title="Nivel de evidencia solo declarado: no hay documento vinculado"
                      >
                        Declarado
                      </span>
                    )}
                    {brecha.esEstructural && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--ui-superficie-2)] text-[var(--ui-enlace)] border border-[var(--ui-borde)] font-semibold">
                        Estructural
                      </span>
                    )}
                    <span
                      className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--ui-boton)] text-white border border-[var(--ui-borde)]"
                      title="Nivel efectivo (0-5)"
                    >
                      NE {brecha.nivelEfectivo}
                    </span>
                    <span
                      className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--ui-boton)] text-white border border-[var(--ui-borde)]"
                      title="Riesgo calculado (0-25)"
                    >
                      R {brecha.riesgo}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded border font-semibold ${tono.fondo} ${tono.texto} ${tono.borde}`}
                    >
                      {brecha.severidad}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}



