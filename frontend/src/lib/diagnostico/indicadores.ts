/**
 * Qué entra en un resultado sellado del diagnóstico (DIAG-03) y con qué forma vuelven sus
 * indicadores. Los calcula el servidor al sellar (features/diagnostico/services/resultados_engine.py)
 * con la misma cuenta que el tablero en modo «verificado»; la prueba de paridad
 * (frontend/tests/diagnostico/paridad.spec.ts y tests/test_diagnostico_resultados.py) compara los
 * dos lados con los mismos casos.
 */
import {
  BANCO_PREGUNTAS,
  normalizarTamano,
  podarBancoPorTamano,
  type PerfilOperacion,
} from "@/lib/bancoPreguntas";
import { usaBancoSGPDP } from "@/lib/normativas";
import type { NormativaAuditoria, RespuestaItemStore } from "@/store/useAuditStore";

/** Cumplimiento, madurez, respaldo con documentos y riesgo que queda, tal como se sellan. */
export interface IndicadoresSellados {
  cumplimiento: boolean;
  brechas_criticas: number;
  madurez: number;
  nivel_madurez: number;
  respaldo_documental: number;
  riesgo_residual: number;
  preguntas_evaluadas: number;
  preguntas_aplicables: number;
  cobertura: number;
}

/**
 * Respuestas que entran en un resultado sellado: las propias (nunca las de referencia) de
 * controles exigibles a la talla y al perfil de la organización.
 */
export function respuestasSellables(
  respuestas: RespuestaItemStore[],
  normativa: NormativaAuditoria,
  tamano: string,
  perfil?: PerfilOperacion
): RespuestaItemStore[] {
  const propias = respuestas.filter((r) => !r.esReferencia);
  if (!usaBancoSGPDP(normativa)) return propias;
  const exigibles = new Set(
    podarBancoPorTamano(BANCO_PREGUNTAS, normalizarTamano(tamano), perfil).map((p) => p.id)
  );
  return propias.filter((r) => r.dimensionId && exigibles.has(r.preguntaId));
}
