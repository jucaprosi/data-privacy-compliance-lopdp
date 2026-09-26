"use client";

import React, { useState } from "react";
import { AlertTriangle } from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { NORMATIVAS, ORDEN_NORMATIVAS, type NormativaId } from "@/lib/normativas";

export default function SelectorNormativa() {
  const { normativaSeleccionada, setNormativa, evidencias } = useAuditStore();
  const [pendiente, setPendiente] = useState<NormativaId | null>(null);

  const elegir = (id: NormativaId) => {
    if (id === normativaSeleccionada) return;
    if (evidencias.length > 0) {
      setPendiente(id);
      return;
    }
    setNormativa(id);
  };

  const confirmarCambio = () => {
    if (pendiente) setNormativa(pendiente);
    setPendiente(null);
  };

  return (
    <section aria-labelledby="selector-normativa-titulo" className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-[#26262b] dark:bg-[#141417]">
      <h3 id="selector-normativa-titulo" className="mb-3 text-xs font-bold uppercase tracking-wider text-zinc-900 dark:text-white">
        Selecciona la normativa
      </h3>
      <select
        id="selector-normativa"
        aria-labelledby="selector-normativa-titulo"
        value={normativaSeleccionada ?? ""}
        onChange={(e) => elegir(e.target.value as NormativaId)}
        className="min-h-11 w-full cursor-pointer rounded-lg border border-zinc-200 bg-zinc-50 px-3.5 py-2.5 text-xs font-semibold text-zinc-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#9a3bf1]/60 dark:border-[#26262b] dark:bg-[#0a0a0c] dark:text-zinc-100"
      >
        <option value="" disabled>
          Selecciona una normativa…
        </option>
        {ORDEN_NORMATIVAS.map((id) => (
          <option key={id} value={id}>
            {NORMATIVAS[id].nombre}
            {NORMATIVAS[id].bancoDisponible ? "" : " (banco en preparación)"}
          </option>
        ))}
      </select>
      {pendiente && (
        <div role="alertdialog" className="mt-3 space-y-2.5 rounded-lg border border-[#ffab00]/40 bg-[#ffab00]/10 p-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#ffab00]" />
            <p className="text-[11px] leading-relaxed text-zinc-700 dark:text-zinc-300">
              Cambiar a {NORMATIVAS[pendiente].nombre} eliminará las evidencias registradas para la normativa actual.
            </p>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setPendiente(null)} className="cursor-pointer rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-[11px] font-semibold text-zinc-700 dark:border-[#26262b] dark:bg-[#141417] dark:text-zinc-300">
              Cancelar
            </button>
            <button type="button" onClick={confirmarCambio} className="cursor-pointer rounded-md bg-[#ffab00] px-3 py-1.5 text-[11px] font-semibold text-[#141417]">
              Cambiar normativa
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
