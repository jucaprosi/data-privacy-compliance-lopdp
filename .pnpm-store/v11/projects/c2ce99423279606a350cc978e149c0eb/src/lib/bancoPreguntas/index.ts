/**
 * Banco canónico de preguntas del assessment SGPDP.
 *
 * Los 80 controles se distribuyen en tres bloques por dimensión y se ensamblan
 * aquí en un único banco ordenado por identificador. El consumidor no debe leer
 * los bloques directamente: siempre a través de este módulo, para que la
 * numeración y el orden queden garantizados en un solo punto.
 */

import { BLOQUE_1 } from "@/lib/bancoPreguntas/bloque1";
import { BLOQUE_2 } from "@/lib/bancoPreguntas/bloque2";
import { BLOQUE_3 } from "@/lib/bancoPreguntas/bloque3";
import type { PreguntaAssessment } from "@/lib/bancoPreguntas/tipos";

export const BANCO_PREGUNTAS: readonly PreguntaAssessment[] = [
  ...BLOQUE_1,
  ...BLOQUE_2,
  ...BLOQUE_3,
].sort((a, b) => a.id - b.id);

export const TOTAL_CONTROLES = BANCO_PREGUNTAS.length;

export * from "@/lib/bancoPreguntas/tipos";
