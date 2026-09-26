import type { BrechaDetectada, ResultadoDimension } from "@/store/useAuditStore";

/** El responsable habilita el trabajo; después se atienden los controles estructurales. */
export function ordenarDimensionesPorPrioridad(
  dimensiones: readonly ResultadoDimension[],
  brechas: readonly BrechaDetectada[]
): ResultadoDimension[] {
  const estructurales = new Map<string, number>();
  for (const brecha of brechas) {
    if (brecha.esEstructural) {
      estructurales.set(brecha.dimensionId, (estructurales.get(brecha.dimensionId) ?? 0) + 1);
    }
  }
  const grupo = (dimension: ResultadoDimension) =>
    dimension.id === "D01" ? 0 : (estructurales.get(dimension.id) ?? 0) > 0 ? 1 : 2;

  return [...dimensiones].sort((a, b) =>
    grupo(a) - grupo(b)
    || (estructurales.get(b.id) ?? 0) - (estructurales.get(a.id) ?? 0)
    || b.brechasCriticas - a.brechasCriticas
    || b.brechasAltas - a.brechasAltas
    || a.score - b.score
    || a.id.localeCompare(b.id)
  );
}

export function brechaPrioritaria(brechas: readonly BrechaDetectada[]): BrechaDetectada | undefined {
  return [...brechas].sort((a, b) =>
    Number(b.esEstructural) - Number(a.esEstructural)
    || (b.severidad === "Crítico" ? 1 : 0) - (a.severidad === "Crítico" ? 1 : 0)
    || b.riesgo - a.riesgo
  )[0];
}
