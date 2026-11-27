// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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
    <section aria-labelledby="selector-normativa-titulo" className="rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 shadow-sm">
      <h3 id="selector-normativa-titulo" className="mb-3 text-xs font-bold uppercase tracking-wider text-[var(--foreground)]">
        Selecciona la normativa
      </h3>
      <select
        id="selector-normativa"
        aria-labelledby="selector-normativa-titulo"
        value={normativaSeleccionada ?? ""}
        onChange={(e) => elegir(e.target.value as NormativaId)}
        className="min-h-11 w-full cursor-pointer rounded-lg border border-[var(--ui-borde-control)] bg-[var(--ui-campo)] px-3.5 py-2.5 text-xs font-semibold text-[var(--foreground)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ui-primario)]"
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
        <div role="alertdialog" className="mt-3 space-y-2.5 rounded-lg border border-[var(--ui-aviso-borde)] bg-[var(--ui-aviso-fondo)] p-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--ui-aviso-texto)]" />
            <p className="text-[11px] leading-relaxed text-[var(--ui-aviso-texto)]">
              Cambiar a {NORMATIVAS[pendiente].nombre} eliminará las evidencias registradas para la normativa actual.
            </p>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setPendiente(null)} className="cursor-pointer rounded-md border border-[var(--ui-borde-control)] bg-[var(--ui-superficie)] px-3 py-1.5 text-[11px] font-semibold text-[var(--foreground)]">
              Cancelar
            </button>
            <button type="button" onClick={confirmarCambio} className="cursor-pointer rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-[11px] font-semibold text-[var(--ui-primario-texto)]">
              Cambiar normativa
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
