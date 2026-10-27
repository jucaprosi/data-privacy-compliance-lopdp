"use client";

import { BookOpenCheck } from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import SelectorNormativa from "@/components/config/SelectorNormativa";
import CargaEvidencias from "@/components/config/CargaEvidencias";
import { NORMATIVAS } from "@/lib/normativas";
import DiagnosticCanvas from "@/components/DiagnosticCanvas";

export default function NormativaWorkspace() {
  const normativaSeleccionada = useAuditStore((state) => state.normativaSeleccionada);
  const preguntaActualIndex = useAuditStore((state) => state.preguntaActualIndex);

  return (
    <div className="mx-auto max-w-5xl space-y-5 pb-10">
      <header className="flex items-center gap-2 border-b border-[var(--ui-borde)] pb-3">
        <BookOpenCheck className="h-5 w-5 text-[#9a3bf1]" />
        <h2 className="text-lg font-bold text-zinc-900 dark:text-white">Normativa</h2>
      </header>
      <SelectorNormativa />
      {normativaSeleccionada && (
        <>
          {NORMATIVAS[normativaSeleccionada].bancoDisponible && preguntaActualIndex === 0 && (
            <CargaEvidencias key={normativaSeleccionada} />
          )}
          {NORMATIVAS[normativaSeleccionada].bancoDisponible ? (
            <DiagnosticCanvas />
          ) : (
            <p className="rounded-xl border border-dashed border-[var(--ui-borde)] p-4 text-xs text-[var(--ui-texto-suave)]">
              El banco de preguntas de {NORMATIVAS[normativaSeleccionada].etiquetaCorta} aún está en preparación.
              La evaluación se habilitará cuando el banco esté disponible.
            </p>
          )}
        </>
      )}
    </div>
  );
}
