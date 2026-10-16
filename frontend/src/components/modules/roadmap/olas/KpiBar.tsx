"use client";

import React from "react";

import type { RoadmapKpis } from "@/types/roadmap";

export interface KpiBarProps {
  kpis: RoadmapKpis | null;
}

function Indicador({ etiqueta, valor, testId }: { etiqueta: string; valor: number; testId: string }) {
  return (
    <div className="rounded-lg bg-[#0a0a0c] border border-[#26262b] p-3">
      <dt className="text-[10px] uppercase tracking-wider font-semibold text-zinc-500">{etiqueta}</dt>
      <dd data-testid={testId} className="text-2xl font-bold text-white mt-1">
        {valor}
      </dd>
    </div>
  );
}

export function KpiBar({ kpis }: KpiBarProps) {
  if (!kpis) {
    return (
      <p role="status" className="text-xs text-zinc-400">
        Los indicadores aún no están disponibles.
      </p>
    );
  }
  const porcentaje = Math.round(kpis.porcentaje_avance ?? (kpis.total ? (kpis.completadas * 100) / kpis.total : 0));

  return (
    <section aria-label="Indicadores de avance" className="space-y-3">
      <div className="flex items-center justify-between text-xs text-zinc-300">
        <span id="kpi-avance-etiqueta">Avance de la hoja de ruta</span>
        <span data-testid="kpi-porcentaje" className="font-semibold text-white">
          {porcentaje} %
        </span>
      </div>
      <div
        role="progressbar"
        aria-labelledby="kpi-avance-etiqueta"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={porcentaje}
        className="h-2 w-full rounded-full bg-[#26262b] overflow-hidden"
      >
        <div className="h-full bg-[#3892f3]" style={{ width: `${porcentaje}%` }} />
      </div>
      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Indicador etiqueta="Tareas" valor={kpis.total} testId="kpi-total" />
        <Indicador etiqueta="Completadas" valor={kpis.completadas} testId="kpi-completadas" />
        <Indicador etiqueta="Críticas" valor={kpis.criticas} testId="kpi-criticas" />
        <Indicador etiqueta="Prioridad alta" valor={kpis.altas} testId="kpi-altas" />
      </dl>
    </section>
  );
}

export default KpiBar;
