"use client";
/**
 * DIAG-14, reescrita por DIAG-07: junto a cada control de nivel y de evidencia explica a quien no puede
 * guardar por qué. Desde DIAG-07 responde la persona asignada a cada dominio (o el administrador) y el
 * DPO revisa y sella; por eso ya no ofrece «Ver como DPO».
 */
import { Lock } from "lucide-react";

/** Qué control acompaña la nota (solo cambia el identificador de prueba en quien la usa). */
export type AccionSoloDpo = "asignar el nivel" | "registrar la evidencia";

export const TEXTO_QUIEN_RESPONDE =
  "Responde esta pregunta la persona asignada a su dominio. El DPO revisa las respuestas y sella el diagnóstico.";

export default function NotaSoloDpo({
  testId,
}: {
  roles: readonly string[];
  accion: AccionSoloDpo;
  testId: string;
}) {
  return (
    <p
      data-testid={testId}
      className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-[var(--ui-texto-suave)] leading-relaxed"
    >
      <Lock aria-hidden="true" className="w-3 h-3 shrink-0" />
      <span>{TEXTO_QUIEN_RESPONDE}</span>
    </p>
  );
}
