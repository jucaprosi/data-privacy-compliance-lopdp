/**
 * Tipos y poda adaptativa del banco de preguntas del assessment SGPDP.
 *
 * Doctrina 9 del PRD (Antecedencia Paramétrica y Poda Ontológica): la ficha
 * organizacional antecede al cuestionario y determina qué controles son
 * exigibles. Un control que presupone estructura inexistente en la organización
 * no se formula: preguntarlo produce una brecha artificial que contamina el
 * scoring sin describir un incumplimiento real.
 *
 * La adaptación opera en dos planos:
 *   1. Número  — cada control declara la talla mínima desde la que aplica.
 *   2. Redacción — un mismo control se enuncia según la estructura esperable
 *      en esa talla, sin rebajar la obligación legal subyacente.
 */

import type { DimensionId } from "@/lib/dimensionesSGPDP";
import { ajustePorPerfil, type PerfilOperacion } from "@/lib/bancoPreguntas/perfil";

/** Tallas organizacionales reconocidas, en orden creciente de exigencia. */
export type TamanoEmpresa = "micro" | "pequena" | "mediana" | "corporativo";

export const ORDEN_TAMANO: readonly TamanoEmpresa[] = [
  "micro",
  "pequena",
  "mediana",
  "corporativo",
] as const;

export interface TamanoDescriptor {
  id: TamanoEmpresa;
  etiqueta: string;
  rangoEmpleados: string;
  rango: number;
}

export const TAMANOS_EMPRESA: readonly TamanoDescriptor[] = [
  { id: "micro", etiqueta: "Organización micro", rangoEmpleados: "1-9", rango: 0 },
  { id: "pequena", etiqueta: "Organización pequeña", rangoEmpleados: "10-49", rango: 1 },
  { id: "mediana", etiqueta: "Organización mediana", rangoEmpleados: "50-199", rango: 2 },
  { id: "corporativo", etiqueta: "Corporativo", rangoEmpleados: "> 200", rango: 3 },
] as const;

/** Variantes de texto por talla. La ausencia de una talla hereda la inmediata inferior. */
export type TextoPorTamano = Partial<Record<TamanoEmpresa, string>>;

export interface PreguntaAssessment {
  /** Identificador estable 1-80, alineado con el banco de referencia. */
  id: number;
  dimensionId: DimensionId;
  /** Nombre corto del control, el que se muestra en el registro de brechas. */
  control: string;
  /** Enunciado base, redactado para la talla declarada en tamanoMinimo. */
  enunciado: string;
  /** Reformulaciones del enunciado para tallas superiores. */
  enunciadoPorTamano?: TextoPorTamano;
  referenciaNormativa: string;
  /** Criticidad 1-5: pondera el riesgo del control en el cálculo. */
  criticidad: number;
  evidenciaEsperada: string;
  evidenciaPorTamano?: TextoPorTamano;
  /** Talla a partir de la cual el control entra al cuestionario. */
  tamanoMinimo: TamanoEmpresa;
  /** Control habilitador: su ausencia degrada el nivel global de madurez. */
  esEstructural?: boolean;
}

/** Vista de una pregunta ya resuelta para una talla concreta. */
export interface PreguntaResuelta extends PreguntaAssessment {
  enunciadoVigente: string;
  evidenciaVigente: string;
  esCritica: boolean;
  riesgoBase: number;
}

/**
 * Traduce la etiqueta de tamaño que persiste la ficha organizacional a la talla
 * canónica. La ficha guarda cadenas legibles ("Organización mediana (50-199)"), así
 * que el emparejamiento se hace por palabra clave y no por igualdad exacta.
 */
export function normalizarTamano(etiqueta: string | undefined): TamanoEmpresa {
  const texto = (etiqueta ?? "").toLowerCase();
  if (texto.includes("micro")) return "micro";
  if (texto.includes("pequeñ") || texto.includes("pequen")) return "pequena";
  if (texto.includes("median")) return "mediana";
  if (texto.includes("corporativ") || texto.includes("grande")) return "corporativo";
  // Sin ficha parametrizada se asume la talla más exigente: es preferible
  // formular un control de más que omitir una obligación aplicable.
  return "corporativo";
}

/**
 * Etiqueta de tamaño de la ficha según el total de personas que trabajan para la
 * organización: empleados directos afiliados al IESS más personas bajo contrato
 * de servicios (cuentas contables de servicios). Es el criterio verificable.
 */
export function etiquetaTamanoPorPersonas(total: number): string {
  if (total >= 200) return "Corporativo (> 200)";
  if (total >= 50) return "Organización mediana (50-199)";
  if (total >= 10) return "Organización pequeña (10-49)";
  return "Organización micro (1-9)";
}

/**
 * Etiqueta vigente de la ficha para una cadena guardada. Las fichas creadas antes
 * del cambio de nomenclatura ("Mediana Empresa (50-199)") se muestran con la
 * etiqueta actual sin alterar el dato persistido.
 */
export function etiquetaFichaDeTamano(etiqueta: string | undefined): string {
  if (!etiqueta) return "";
  const rango = rangoDeTamano(normalizarTamano(etiqueta));
  return ["Organización micro (1-9)", "Organización pequeña (10-49)", "Organización mediana (50-199)", "Corporativo (> 200)"][rango];
}

export function rangoDeTamano(tamano: TamanoEmpresa): number {
  return TAMANOS_EMPRESA.find((t) => t.id === tamano)?.rango ?? 3;
}

/**
 * Resuelve el texto vigente para una talla: toma la variante declarada para esa
 * talla o, en su defecto, la más específica por debajo de ella.
 */
function resolverTexto(
  base: string,
  variantes: TextoPorTamano | undefined,
  tamano: TamanoEmpresa
): string {
  if (!variantes) return base;
  const rangoObjetivo = rangoDeTamano(tamano);
  let elegido = base;
  for (const talla of ORDEN_TAMANO) {
    if (rangoDeTamano(talla) > rangoObjetivo) break;
    const variante = variantes[talla];
    if (variante) elegido = variante;
  }
  return elegido;
}

/**
 * Indica si un control es exigible. La talla fija la base; el perfil de
 * operación (si existe) incorpora controles por exposición y descarta los que
 * presuponen algo que la organización no hace.
 */
export function aplicaATamano(
  pregunta: PreguntaAssessment,
  tamano: TamanoEmpresa,
  perfil?: PerfilOperacion
): boolean {
  const ajuste = ajustePorPerfil(perfil);
  if (ajuste.incluidas.has(pregunta.id)) return true;
  if (ajuste.descartadas.has(pregunta.id)) return false;
  return rangoDeTamano(tamano) >= rangoDeTamano(pregunta.tamanoMinimo);
}

/**
 * Poda el banco para una talla y un perfil, y resuelve los textos de cada control.
 * Invariante del PRD: el resultado nunca excede los 80 controles visibles.
 */
export function podarBancoPorTamano(
  banco: readonly PreguntaAssessment[],
  tamano: TamanoEmpresa,
  perfil?: PerfilOperacion
): PreguntaResuelta[] {
  const ajuste = ajustePorPerfil(perfil);
  return banco
    .filter((p) => aplicaATamano(p, tamano, perfil))
    .slice(0, 80)
    .map((p) => {
      const criticidad = ajuste.criticidadMaxima.has(p.id) ? 5 : p.criticidad;
      return {
        ...p,
        criticidad,
        enunciadoVigente: resolverTexto(p.enunciado, p.enunciadoPorTamano, tamano),
        evidenciaVigente: resolverTexto(p.evidenciaEsperada, p.evidenciaPorTamano, tamano),
        esCritica: criticidad >= 5,
        riesgoBase: criticidad * 2,
      };
    });
}

/** Conteo de controles aplicables por talla, para mostrar el alcance de la sesión. */
export function conteoPorTamano(
  banco: readonly PreguntaAssessment[]
): Record<TamanoEmpresa, number> {
  return ORDEN_TAMANO.reduce(
    (acc, talla) => {
      acc[talla] = banco.filter((p) => aplicaATamano(p, talla)).length;
      return acc;
    },
    {} as Record<TamanoEmpresa, number>
  );
}
