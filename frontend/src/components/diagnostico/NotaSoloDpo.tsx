"use client";
/**
 * DIAG-14, retirada por DIAG-07: la nota por pregunta duplicaba la franja del lienzo, que ya dice a cada
 * rol quién responde, quién sella y qué puede hacer. El UX/UI pidió que nunca haya dos notas a la vez,
 * así que no muestra nada. Se conserva para no tocar las llamadas del lienzo fuera de su propiedad.
 */

/** Qué control acompaña la nota (solo cambia el identificador de prueba en quien la usa). */
export type AccionSoloDpo = "asignar el nivel" | "registrar la evidencia";

export default function NotaSoloDpo(_props: { roles: readonly string[]; accion: AccionSoloDpo; testId: string }) {
  return null;
}
