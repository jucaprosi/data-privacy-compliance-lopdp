/**
 * Catálogo canónico de las 10 dimensiones del SGPDP y su metodología de scoring.
 * Fuente: Matriz de Madurez SGPDP (modelo SMARTCIDI) alineada a LOPDP Ecuador.
 *
 * Metodología (invariante del modelo):
 *   Nivel efectivo   = MIN(nivel asignado, nivel evidencia + 1)
 *   Riesgo           = (5 - nivel efectivo) x criticidad
 *   Score dimension  = SUMA((nivel efectivo / 5) x criticidad) / SUMA(criticidad)
 *   Madurez global   = SUMA(score dimension x peso dimension)
 *
 * El score de dimensión se pondera por criticidad y su denominador abarca todos
 * los controles exigibles: un control sin responder computa como cero, no se
 * excluye del cálculo. Es la única forma de que el avance parcial no se lea como
 * madurez alcanzada.
 *
 * Doctrina 4 del PRD: el score ponderado nunca puede enmascarar una brecha
 * estructural. Un control estructural en nivel bajo degrada el nivel final
 * con independencia del promedio obtenido.
 */

export type DimensionId =
  | "D01"
  | "D02"
  | "D03"
  | "D04"
  | "D05"
  | "D06"
  | "D07"
  | "D08"
  | "D09"
  | "D10";

export interface DimensionSGPDP {
  id: DimensionId;
  nombre: string;
  peso: number;
  dominiosOrigen: string[];
}

/** Las 10 dimensiones ponderadas. La suma de pesos es exactamente 1.00. */
export const DIMENSIONES_SGPDP: readonly DimensionSGPDP[] = [
  {
    id: "D01",
    nombre: "Gobierno y responsabilidad proactiva",
    peso: 0.12,
    dominiosOrigen: ["G01", "G13"],
  },
  {
    id: "D02",
    nombre: "Inventario, RAT, finalidades y legitimación",
    peso: 0.14,
    dominiosOrigen: ["G02", "G03"],
  },
  {
    id: "D03",
    nombre: "Transparencia e información al titular",
    peso: 0.08,
    dominiosOrigen: ["G03"],
  },
  {
    id: "D04",
    nombre: "Derechos de titulares",
    peso: 0.08,
    dominiosOrigen: ["G04"],
  },
  {
    id: "D05",
    nombre: "Procesos críticos y ciclo de vida de datos",
    peso: 0.1,
    dominiosOrigen: ["G05", "G11"],
  },
  {
    id: "D06",
    nombre: "Encargados, proveedores y transferencias",
    peso: 0.1,
    dominiosOrigen: ["G09", "G10"],
  },
  {
    id: "D07",
    nombre: "Seguridad de datos personales",
    peso: 0.14,
    dominiosOrigen: ["G08"],
  },
  {
    id: "D08",
    nombre: "Incidentes y vulneraciones",
    peso: 0.08,
    dominiosOrigen: ["G12"],
  },
  {
    id: "D09",
    nombre: "Riesgos, EIPD, LIA y privacidad desde el diseño",
    peso: 0.11,
    dominiosOrigen: ["G06", "G07", "G15", "G16"],
  },
  {
    id: "D10",
    nombre: "Capacitación, cultura, auditoría y mejora continua",
    peso: 0.05,
    dominiosOrigen: ["G14"],
  },
] as const;

/** Índice de acceso directo por identificador de dimensión. */
export const DIMENSION_POR_ID: Readonly<Record<DimensionId, DimensionSGPDP>> =
  Object.fromEntries(DIMENSIONES_SGPDP.map((d) => [d.id, d])) as Record<
    DimensionId,
    DimensionSGPDP
  >;

/**
 * Resuelve la dimensión a la que pertenece un dominio JUBYS (G01-G16).
 * Un dominio sin mapeo explícito se imputa a Gobierno para no perder el control
 * del cómputo ponderado.
 */
export function dimensionDeDominio(dominioId: string): DimensionId {
  const dominio = dominioId.trim().toUpperCase();
  const encontrada = DIMENSIONES_SGPDP.find((d) =>
    d.dominiosOrigen.includes(dominio)
  );
  return encontrada?.id ?? "D01";
}

/**
 * Controles estructurales habilitadores. Su nivel efectivo bajo degrada el
 * nivel de madurez global porque el resto del sistema no puede demostrarse
 * sin ellos (trazabilidad del inventario hacia riesgos, avisos y derechos).
 */
export interface ControlEstructural {
  preguntaId: number;
  nombre: string;
  dimension: DimensionId;
  accionPrioritaria: string;
}

export const CONTROLES_ESTRUCTURALES: readonly ControlEstructural[] = [
  {
    preguntaId: 9,
    nombre: "Inventario de tratamientos",
    dimension: "D02",
    accionPrioritaria:
      "Levantar o actualizar el inventario de tratamientos con dueños por proceso.",
  },
  {
    preguntaId: 10,
    nombre: "Registro de Actividades de Tratamiento (RAT)",
    dimension: "D02",
    accionPrioritaria:
      "Construir o actualizar el RAT sobre procesos reales con evidencia de validación.",
  },
  {
    preguntaId: 13,
    nombre: "Datos sensibles y de mayor riesgo",
    dimension: "D02",
    accionPrioritaria:
      "Clasificar datos sensibles y definir controles reforzados por tratamiento.",
  },
  {
    preguntaId: 28,
    nombre: "Verificación de identidad",
    dimension: "D04",
    accionPrioritaria:
      "Definir criterios de verificación de identidad y representación.",
  },
] as const;

export const PREGUNTAS_ESTRUCTURALES: readonly number[] =
  CONTROLES_ESTRUCTURALES.map((c) => c.preguntaId);

/** Escala de madurez 1-5 empleada por la matriz de assessment. */
export interface NivelMadurez {
  nivel: number;
  etiqueta: string;
  descripcion: string;
  umbralMinimo: number;
}

export const NIVELES_MADUREZ: readonly NivelMadurez[] = [
  {
    nivel: 1,
    etiqueta: "Inicial",
    descripcion: "Prácticas ausentes o reactivas, sin formalización.",
    umbralMinimo: 0,
  },
  {
    nivel: 2,
    etiqueta: "Básico / Repetible",
    descripcion: "Prácticas incipientes con soporte documental parcial.",
    umbralMinimo: 40,
  },
  {
    nivel: 3,
    etiqueta: "Definido",
    descripcion: "Procesos documentados y comunicados a los responsables.",
    umbralMinimo: 60,
  },
  {
    nivel: 4,
    etiqueta: "Gestionado",
    descripcion: "Procesos medidos, con indicadores y revisión periódica.",
    umbralMinimo: 75,
  },
  {
    nivel: 5,
    etiqueta: "Optimizado",
    descripcion: "Mejora continua demostrable y trazable extremo a extremo.",
    umbralMinimo: 90,
  },
] as const;

/** Índice de acceso directo por número de nivel (1-5). */
export const NIVELES_MADUREZ_INDEX: Readonly<Record<number, NivelMadurez>> =
  Object.fromEntries(NIVELES_MADUREZ.map((n) => [n.nivel, n])) as Record<
    number,
    NivelMadurez
  >;

/** Traduce un score porcentual (0-100) al nivel de madurez que le corresponde. */
export function nivelDesdeScore(scorePorcentual: number): NivelMadurez {
  let resultado = NIVELES_MADUREZ[0];
  for (const nivel of NIVELES_MADUREZ) {
    if (scorePorcentual >= nivel.umbralMinimo) {
      resultado = nivel;
    }
  }
  return resultado;
}

/** Cota superior de nivel cuando existe al menos un control estructural degradado. */
export const NIVEL_TOPE_BRECHA_ESTRUCTURAL = 2;

/** Nivel efectivo por debajo del cual un control estructural se considera degradado. */
export const UMBRAL_DEGRADACION_ESTRUCTURAL = 3;

/**
 * Un control de criticidad máxima es bloqueante: su nivel efectivo bajo topa el
 * nivel global igual que un control estructural. Los cuatro estructurales del
 * catálogo son un subconjunto de este criterio, no una lista aparte.
 */
export const CRITICIDAD_BLOQUEANTE = 5;

/**
 * Criticidad a partir de la cual la falta de evidencia pesa por sí sola, y cota
 * de nivel que impone: un control de alta criticidad sostenido solo en la
 * declaración no permite acreditar procesos gestionados.
 */
export const CRITICIDAD_EVIDENCIA_EXIGIBLE = 4;
export const UMBRAL_EVIDENCIA_EXIGIBLE = 2;
export const NIVEL_TOPE_EVIDENCIA_INSUFICIENTE = 3;

/**
 * Cobertura mínima para que el resultado sea emitible. Por debajo de este
 * porcentaje el assessment no califica: informa nivel 0, no un nivel bajo.
 */
export const COBERTURA_MINIMA_EMISION = 60;

/** Umbrales de riesgo (5 - nivel efectivo) x criticidad para clasificar brechas. */
export const RIESGO_BRECHA_CRITICA = 15;
export const RIESGO_BRECHA_ALTA = 9;

/**
 * Rango de nivel de evidencia (E0-E3) coherente con cada estado de
 * cumplimiento declarado. Evita registrar combinaciones que se contradicen a
 * sí mismas (p. ej. "No Conforme" sostenido en evidencia "Auditable /
 * Certificado", o "Conforme" sin ningún soporte). Los rangos se solapan en un
 * punto ("Parcial" y "Conforme" comparten E2) porque la frontera entre
 * estados es continua, no un salto discreto.
 *
 * "Pendiente" no tiene rango: la pregunta aún no tiene una declaración de
 * conformidad que el nivel de evidencia pueda respaldar o contradecir.
 */
export const RANGO_EVIDENCIA_POR_CUMPLE: Readonly<
  Record<"Conforme" | "Parcial" | "No Conforme", readonly [number, number]>
> = {
  "No Conforme": [0, 1],
  Parcial: [1, 2],
  Conforme: [2, 3],
};
