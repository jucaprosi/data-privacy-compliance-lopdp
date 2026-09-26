"use client";

import React, { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, ClipboardList, Info, ShieldAlert } from "lucide-react";
import {
  useAuditStore,
  type HallazgoNIIF18,
  type RecomendacionesNIIF18,
} from "@/store/useAuditStore";

const ESTADO: Record<string, { texto: string; color: string }> = {
  REQUIERE_CORRECCION: { texto: "Requiere corrección", color: "text-[#ff1744] border-[#ff1744]/40 bg-[#ff1744]/10" },
  CON_OBSERVACIONES: { texto: "Con observaciones", color: "text-[#ffab00] border-[#ffab00]/40 bg-[#ffab00]/10" },
  LISTO_PARA_PRESENTAR: { texto: "Listo para presentar", color: "text-[#00c853] border-[#00c853]/40 bg-[#00c853]/10" },
};

const SEVERIDAD: Record<HallazgoNIIF18["severidad"], { color: string; Icono: typeof Info }> = {
  ALTA: { color: "text-[#ff1744]", Icono: ShieldAlert },
  MEDIA: { color: "text-[#ffab00]", Icono: AlertTriangle },
  BAJA: { color: "text-[#3892f3]", Icono: Info },
  INFO: { color: "text-zinc-400", Icono: Info },
};

const pct = (v: number | null | undefined) => (v == null ? "n/d" : `${(v * 100).toFixed(1)}%`);
const dinero = (v: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(v);

export default function NiifDiagnosticoView() {
  const { niif18Data, mpmRecords } = useAuditStore();
  const [plan, setPlan] = useState<RecomendacionesNIIF18 | null>(null);
  const [error, setError] = useState<string | null>(null);

  // El plan se recalcula cuando cambia la clasificación o las MPM registradas.
  useEffect(() => {
    if (!niif18Data) return;
    let vigente = true;
    fetch("/api/v1/niif18/informe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cuentas: niif18Data.cuentas, mpm: mpmRecords }),
    })
      .then((res) => {
        if (!res.ok) throw new Error("No se pudo generar el diagnóstico.");
        return res.json();
      })
      .then((data) => {
        if (vigente) {
          setPlan(data.recomendaciones);
          setError(null);
        }
      })
      .catch((e: unknown) => vigente && setError(e instanceof Error ? e.message : String(e)));
    return () => {
      vigente = false;
    };
  }, [niif18Data, mpmRecords]);

  if (!niif18Data?.diagnostico) {
    return (
      <div className="flex items-center justify-center h-full text-zinc-500">
        No hay balance procesado. Carga un Balance de Comprobación en la Ingesta.
      </div>
    );
  }

  const { diagnostico, indicadores } = niif18Data;
  const estado = ESTADO[diagnostico.estado];

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
      <div className="flex flex-wrap items-center justify-between gap-4 bg-[#141417] border border-[#26262b] rounded-xl p-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center">
            <ClipboardList className="w-5 h-5 mr-2 text-[#9a3bf1]" />
            Diagnóstico del Balance y Plan de Implementación
          </h2>
          <p className="text-sm text-zinc-400 mt-1">
            {diagnostico.total_cuentas} cuentas analizadas · balanza {diagnostico.cuadre.cuadra ? "cuadrada" : `descuadrada por ${dinero(diagnostico.cuadre.diferencia)}`}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`rounded-lg border px-3 py-1.5 text-xs font-semibold ${estado.color}`}>{estado.texto}</span>
          <span className="text-2xl font-bold text-white">{diagnostico.puntaje}<span className="text-sm text-zinc-500">/100</span></span>
        </div>
      </div>

      {indicadores && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            ["Margen operativo", pct(indicadores.margen_operativo)],
            ["Margen neto", pct(indicadores.margen_neto)],
            ["Tasa efectiva de impuestos", pct(indicadores.tasa_efectiva_impuestos)],
            ["EBITDA referencial", dinero(indicadores.ebitda_referencial)],
          ].map(([titulo, valor]) => (
            <div key={titulo} className="bg-[#141417] border border-[#26262b] rounded-xl p-4">
              <div className="text-[10px] uppercase tracking-wider text-zinc-500">{titulo}</div>
              <div className="mt-1 text-lg font-bold text-white">{valor}</div>
            </div>
          ))}
        </div>
      )}

      <section className="bg-[#141417] border border-[#26262b] rounded-xl p-5 space-y-3">
        <h3 className="text-sm font-bold text-white">Hallazgos</h3>
        {diagnostico.hallazgos.length === 0 && (
          <p className="flex items-center gap-2 text-xs text-[#00c853]"><CheckCircle2 className="w-4 h-4" /> Sin hallazgos.</p>
        )}
        {diagnostico.hallazgos.map((h) => {
          const { color, Icono } = SEVERIDAD[h.severidad];
          return (
            <div key={h.codigo} className="rounded-lg border border-[#26262b] bg-[#0a0a0c] p-3">
              <div className={`flex items-center gap-2 text-xs font-semibold ${color}`}>
                <Icono className="w-4 h-4 shrink-0" />
                <span>{h.codigo} · {h.severidad}</span>
                <span className="text-white">{h.titulo}</span>
              </div>
              <p className="mt-1 text-xs text-zinc-400">{h.detalle}</p>
              {h.cuentas.length > 0 && <p className="mt-1 text-[11px] font-mono text-zinc-500">Cuentas: {h.cuentas.join(", ")}</p>}
              <p className="mt-1 text-[10px] text-zinc-600">{h.referencia}</p>
            </div>
          );
        })}
      </section>

      {error && <p className="text-xs text-[#ff1744]">{error}</p>}

      {plan && (
        <>
          <section className="bg-[#141417] border border-[#26262b] rounded-xl p-5 space-y-3">
            <h3 className="text-sm font-bold text-white">Recomendaciones priorizadas</h3>
            {plan.acciones.map((a, i) => (
              <div key={i} className="flex gap-3 rounded-lg border border-[#26262b] bg-[#0a0a0c] p-3">
                <span className="h-fit rounded bg-[#9a3bf1]/15 px-2 py-0.5 text-[10px] font-bold text-[#9a3bf1]">{a.prioridad}</span>
                <div className="min-w-0">
                  <p className="text-xs text-white"><span className="font-semibold">{a.tipo}:</span> {a.accion}</p>
                  <p className="mt-1 text-[10px] text-zinc-500">{a.fundamento}</p>
                </div>
              </div>
            ))}
          </section>

          <section className="bg-[#141417] border border-[#26262b] rounded-xl p-5 space-y-3">
            <h3 className="text-sm font-bold text-white">Hoja de ruta de implementación</h3>
            <ol className="space-y-2">
              {plan.hoja_de_ruta.map((f) => (
                <li key={f.fase} className="rounded-lg border border-[#26262b] bg-[#0a0a0c] p-3">
                  <p className="text-xs font-semibold text-white">{f.fase}</p>
                  <p className="mt-1 text-xs text-zinc-400">{f.descripcion}</p>
                  <p className="mt-1 text-[10px] text-zinc-600">{f.referencia}</p>
                </li>
              ))}
            </ol>
          </section>
        </>
      )}

      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => useAuditStore.getState().setActiveView("niif_exportacion")}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded transition-colors cursor-pointer"
        >
          Siguiente Paso: Exportar reportes
        </button>
      </div>
    </div>
  );
}
