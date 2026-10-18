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
import {
  CLAVES_DE_TAMANO,
  TAMANOS_ORGANIZACION,
  claveDeEtiqueta,
  etiquetaDeFicha,
  infoDeTamano,
  tamanoPorPersonas,
  type TamanoOrganizacion,
} from "@/lib/tamanoOrganizacion";

/**
 * Tallas organizacionales reconocidas, en orden creciente de exigencia. Vienen de
 * `lib/tamanoOrganizacion.ts`, la única fuente (sus claves son las del servidor).
 */
export type TamanoEmpresa = TamanoOrganizacion;

export const ORDEN_TAMANO: readonly TamanoEmpresa[] = CLAVES_DE_TAMANO;

export interface TamanoDescriptor {
  id: TamanoEmpresa;
  etiqueta: string;
  rangoEmpleados: string;
  rango: number;
}

export const TAMANOS_EMPRESA: readonly TamanoDescriptor[] = TAMANOS_ORGANIZACION.map((t) => ({
  id: t.clave,
  etiqueta: t.etiqueta,
  rangoEmpleados: t.personas,
  rango: t.rango,
}));

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
 * Traduce la etiqueta de tamaño que persiste la ficha organizacional a la talla canónica. Acepta las
 * etiquetas de todas las versiones de la ficha y la clave del servidor; lo desconocido se trata como
 * la talla más exigente (ver `claveDeEtiqueta`).
 */
export function normalizarTamano(etiqueta: string | undefined): TamanoEmpresa {
  return claveDeEtiqueta(etiqueta);
}

/**
 * Etiqueta de tamaño de la ficha según el total de personas que trabajan para la organización:
 * empleados directos afiliados al IESS más personas bajo contrato de servicios (cuentas contables de
 * servicios). Es el criterio verificable.
 */
export function etiquetaTamanoPorPersonas(total: number): string {
  return etiquetaDeFicha(tamanoPorPersonas(total));
}

/**
 * Etiqueta vigente de la ficha para una cadena guardada. Las fichas creadas con una nomenclatura
 * anterior («Mediana Empresa (50-199)», «Corporativo (> 200)») se muestran con la etiqueta actual sin
 * alterar el dato persistido.
 */
export function etiquetaFichaDeTamano(etiqueta: string | undefined): string {
  if (!etiqueta) return "";
  return etiquetaDeFicha(normalizarTamano(etiqueta));
}

export function rangoDeTamano(tamano: TamanoEmpresa): number {
  return infoDeTamano(tamano).rango;
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
