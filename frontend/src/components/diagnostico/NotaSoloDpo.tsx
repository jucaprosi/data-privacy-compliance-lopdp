"use client";
/**
 * DIAG-14, reescrita por DIAG-07: junto a cada control de nivel y de evidencia explica a quien no puede
 * guardar por qué (salvo al DPO, que ya tiene la franja del lienzo). Desde DIAG-07 responde la persona asignada a cada dominio (o el administrador) y el
 * DPO revisa y sella; por eso ya no ofrece «Ver como DPO».
 */
import { Lock } from "lucide-react";

import { puedeSellar } from "@/lib/diagnostico/roles";

/** Qué control acompaña la nota (solo cambia el identificador de prueba en quien la usa). */
export type AccionSoloDpo = "asignar el nivel" | "registrar la evidencia";

export const TEXTO_QUIEN_RESPONDE = "Responde esta pregunta la persona asignada a su dimensión.";

export default function NotaSoloDpo({
  roles,
  testId,
}: {
  roles: readonly string[];
  accion: AccionSoloDpo;
  testId: string;
}) {
  // Al DPO le basta la franja del lienzo: no lleva una nota en cada pregunta (UX/UI, DIAG-07).
  if (puedeSellar(roles)) return null;
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
