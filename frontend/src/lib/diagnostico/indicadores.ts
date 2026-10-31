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

/** Nivel de una dimensión tal como se sella (DIAG-08): 0 con «Sin evaluación suficiente» si falta cobertura. */
export interface NivelDimensionSellado {
  dimension: string;
  nombre: string;
  nivel: number;
  etiqueta: string;
  score: number;
  cobertura: number;
  brechas_criticas: number;
  brechas_altas: number;
}

/**
 * Indicadores de un resultado sellado. Con la escala nueva (`smartcidi_1_5`) traen los niveles por
 * dimensión y ninguna cifra global; un resultado sellado antes llega con `escala = "anterior"` y se
 * muestra con el aviso, sin convertirlo (DIAG-09 R4).
 */
export interface IndicadoresSellados {
  escala: "smartcidi_1_5" | "anterior";
  cumplimiento: boolean;
  brechas_criticas: number;
  brechas_altas?: number;
  por_dimension?: NivelDimensionSellado[];
  respaldo_documental: number;
  preguntas_evaluadas: number;
  preguntas_aplicables: number;
  cobertura: number;
}

export const AVISO_ESCALA_ANTERIOR =
  "Este diagnóstico se selló con la escala anterior. Vuelve a responder y sellar para ver los niveles por dimensión.";

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
