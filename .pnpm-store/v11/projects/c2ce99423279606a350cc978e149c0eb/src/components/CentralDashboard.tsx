"use client";

import React, { useState } from "react";
import {
  SlidersHorizontal,
  Clock,
  Building2,
  ArrowUpRight,
  GitCommit,
  FlaskConical,
} from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import AssessmentResultPanel from "@/components/dashboard/AssessmentResultPanel";
import AssessmentTasksPanel from "@/components/dashboard/AssessmentTasksPanel";
import tabStyles from "@/components/dashboard/DashboardTabs.module.css";
import { resolverNormativa } from "@/lib/normativas";

export default function CentralDashboard() {
  const [pestana, setPestana] = useState<"informe" | "tasks">("informe");
  const {
    isConfigured,
    companyData,
    normativaSeleccionada,
    timeboxRestante,
    calcularResultadoAssessment,
    setActiveView,
  } = useAuditStore();

  const resultadoAssessment = calcularResultadoAssessment();
  const minutos = Math.floor(timeboxRestante / 60);
  const segundos = timeboxRestante % 60;
  const tiempoFormateado = `${String(minutos).padStart(2, "0")}:${String(segundos).padStart(2, "0")}`;

  if (!isConfigured) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 font-sans animate-in fade-in duration-300">
        <div className="p-8 sm:p-12 rounded-2xl bg-[#141417] border border-[#26262b] text-center space-y-6 shadow-xl">
          <div className="w-16 h-16 rounded-2xl bg-[#1e1e24] border border-[#26262b] mx-auto flex items-center justify-center text-[#9a3bf1] shadow-inner">
            <SlidersHorizontal className="w-8 h-8" />
          </div>
          <div className="space-y-2 max-w-lg mx-auto">
            <span className="text-[10px] font-mono uppercase px-2.5 py-1 rounded bg-[#9a3bf1]/15 text-[#9a3bf1] border border-[#9a3bf1]/30 font-semibold tracking-wider">
              Calibración Pendiente · Módulo 1
            </span>
            <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
              Ficha Organizacional No Parametrizada
            </h2>
            <p className="text-xs text-zinc-400 leading-relaxed">
              El motor de scoring multidimensional y el podado dinámico de dominios LOPDP requieren que establezcas la
              Razón Social, sector económico y marco regulatorio rector.
            </p>
          </div>
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => setActiveView("configuracion")}
              className="w-full sm:w-auto px-5 py-2.5 rounded-lg bg-[#9a3bf1] hover:bg-[#8529e0] text-white text-xs font-semibold flex items-center justify-center space-x-2 transition cursor-pointer shadow-lg shadow-[#9a3bf1]/20 hover:scale-[1.02]"
            >
              <SlidersHorizontal className="w-4 h-4" />
              <span>Configurar Ficha en Panel Izquierdo</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 font-sans pb-12 animate-in fade-in duration-200">
      <div className="p-4 rounded-xl bg-[#141417] border border-[#26262b] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-[#1e1e24] border border-[#26262b] flex items-center justify-center text-[#9a3bf1]">
            <Building2 className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-tight flex items-center space-x-2">
              <span>{companyData.razonSocial || "Entidad en Evaluación"}</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1e1e24] text-zinc-300 border border-[#26262b]">
                {companyData.sector}
              </span>
            </h2>
            <p className="text-[11px] text-zinc-400 font-mono mt-0.5">
              Régimen Rector: <span className="text-zinc-200 font-semibold">{resolverNormativa(normativaSeleccionada).etiquetaCorta}</span> · LOPDP Ecuador 2026
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#0a0a0c] border border-[#26262b] text-[11px] font-mono text-zinc-300">
            <Clock className="w-3.5 h-3.5 text-zinc-400" />
            <span className="text-zinc-500">Timebox:</span>
            <span className="text-white font-bold">{tiempoFormateado}</span>
          </div>
          <button
            type="button"
            onClick={() => setActiveView("auditoria")}
            className="px-3.5 py-1.5 rounded-lg bg-[#1e1e24] hover:bg-[#26262b] border border-[#26262b] text-zinc-300 hover:text-white text-xs font-medium flex items-center space-x-1.5 transition cursor-pointer"
          >
            <GitCommit className="w-3.5 h-3.5 text-[#9a3bf1]" />
            <span>Historial</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveView("diagnostico")}
            className="px-3.5 py-1.5 rounded-lg bg-[#1e1e24] hover:bg-[#26262b] border border-[#26262b] text-white text-xs font-medium flex items-center space-x-1.5 transition cursor-pointer"
          >
            <span>Ir a Preguntas</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-[#9a3bf1]" />
          </button>
        </div>
      </div>

      {resultadoAssessment.soloReferencia && (
        <div className="p-3.5 rounded-xl bg-[#ffab00]/10 border border-[#ffab00]/30 flex items-start gap-3">
          <FlaskConical className="w-4 h-4 text-[#ffab00] shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="text-[11px] font-bold text-[#ffab00] uppercase tracking-wider">
              Resultados de referencia
            </p>
            <p className="text-[11px] text-zinc-300 leading-relaxed">
              Los resultados que siguen provienen del banco de referencia del modelo, no de un
              diagnóstico registrado. Sirven para dimensionar el tablero y no tienen valor
              probatorio: el sellado de snapshots permanece bloqueado hasta que existan
              respuestas propias.
            </p>
          </div>
        </div>
      )}

      <div className={tabStyles.tabs} role="tablist" aria-label="Vistas del diagnóstico">
        <button type="button" role="tab" id="tab-informe" aria-selected={pestana === "informe"}
          aria-controls="panel-informe" className={pestana === "informe" ? tabStyles.active : ""}
          onClick={() => setPestana("informe")}>Informe</button>
        <button type="button" role="tab" id="tab-tasks" aria-selected={pestana === "tasks"}
          aria-controls="panel-tasks" className={pestana === "tasks" ? tabStyles.active : ""}
          onClick={() => setPestana("tasks")}>Tasks · plan de acción</button>
      </div>
      <div id="panel-informe" role="tabpanel" aria-labelledby="tab-informe" hidden={pestana !== "informe"}>
        {pestana === "informe" && <AssessmentResultPanel onShowTasks={() => setPestana("tasks")} />}
      </div>
      <div id="panel-tasks" role="tabpanel" aria-labelledby="tab-tasks" hidden={pestana !== "tasks"}>
        {pestana === "tasks" && <AssessmentTasksPanel />}
      </div>
    </div>
  );
}
