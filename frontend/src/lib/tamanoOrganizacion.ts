/**
 * Una sola fuente del tamaño de la organización.
 *
 * Las claves son las del servidor (`features/organizacion/domain/tamanos.py`, columna
 * `tenants.tamano`, vocabulario cerrado con restricción en la base). Antes había tres listas que no
 * se hablaban: el banco de preguntas, la ficha y el panel de administración, cada una con sus
 * etiquetas, y la ficha guardaba la etiqueta («Organización mediana (50-199)») en lugar de la clave.
 * Ahora todas derivan de este módulo; la prueba `tests/tamano/mapeo.spec.ts` comprueba que las
 * claves coinciden con las del servidor.
 *
 * Módulo puro: sin React, sin red, sin importaciones. Lo usan la ficha, `normalizarTamano` del banco
 * de preguntas y el panel de administración de la Hoja de Ruta.
 */

/** Claves de tamaño, en orden creciente de exigencia. Idénticas a `TamanoOrganizacion` del servidor. */
export type TamanoOrganizacion = "micro" | "pequena" | "mediana" | "corporativo";

export interface InfoTamano {
  clave: TamanoOrganizacion;
  /** Nombre corto, el del panel de administración. */
  etiqueta: string;
  /** Personas que trabajan en la organización, tal como se muestra («1-9»). */
  personas: string;
  /** Posición en el orden de exigencia (0 = la menos exigente). */
  rango: number;
  /** Menos personas que esto ya no es esta talla. */
  desdePersonas: number;
}

export const TAMANOS_ORGANIZACION: readonly InfoTamano[] = [
  { clave: "micro", etiqueta: "Microempresa", personas: "1-9", rango: 0, desdePersonas: 0 },
  { clave: "pequena", etiqueta: "Pequeña empresa", personas: "10-49", rango: 1, desdePersonas: 10 },
  { clave: "mediana", etiqueta: "Mediana empresa", personas: "50-199", rango: 2, desdePersonas: 50 },
  // 200 personas ya es corporativo: la etiqueta no puede decir «> 200», que lo excluiría.
  { clave: "corporativo", etiqueta: "Corporativo", personas: "200 o más", rango: 3, desdePersonas: 200 },
] as const;

export const CLAVES_DE_TAMANO: readonly TamanoOrganizacion[] = TAMANOS_ORGANIZACION.map((t) => t.clave);

/**
 * Talla que se asume cuando no se puede saber: la más exigente. Es preferible formular un control
 * de más que omitir una obligación aplicable (decisión ya vigente del banco de preguntas).
 */
export const TAMANO_SI_SE_DESCONOCE: TamanoOrganizacion = "corporativo";

export function esClaveDeTamano(valor: unknown): valor is TamanoOrganizacion {
  return typeof valor === "string" && (CLAVES_DE_TAMANO as readonly string[]).includes(valor);
}

export function infoDeTamano(clave: TamanoOrganizacion): InfoTamano {
  return TAMANOS_ORGANIZACION.find((t) => t.clave === clave) ?? TAMANOS_ORGANIZACION[TAMANOS_ORGANIZACION.length - 1];
}

/** «Mediana empresa (50-199)»: lo que muestra la ficha y lo que se guarda en ella. */
export function etiquetaDeFicha(clave: TamanoOrganizacion): string {
  const { etiqueta, personas } = infoDeTamano(clave);
  return `${etiqueta} (${personas})`;
}

/** Talla que corresponde a un total de personas (empleados afiliados al IESS más contratados de servicios). */
export function tamanoPorPersonas(total: number): TamanoOrganizacion {
  for (let i = TAMANOS_ORGANIZACION.length - 1; i >= 0; i -= 1) {
    if (total >= TAMANOS_ORGANIZACION[i].desdePersonas) return TAMANOS_ORGANIZACION[i].clave;
  }
  return TAMANOS_ORGANIZACION[0].clave;
}

/**
 * Talla a partir de una etiqueta guardada. Acepta la clave del servidor y las etiquetas de todas las
 * versiones de la ficha («Mediana Empresa (50-199)», «Organización pequeña (10-49)», «Corporativo
 * (> 200)»...): el emparejamiento es por palabra clave, no por igualdad exacta, para no invalidar
 * proyectos ya guardados. Lo desconocido se trata como `TAMANO_SI_SE_DESCONOCE`.
 */
export function claveDeEtiqueta(etiqueta: string | null | undefined): TamanoOrganizacion {
  const texto = (etiqueta ?? "").toLowerCase();
  if (texto.includes("micro")) return "micro";
  if (texto.includes("pequeñ") || texto.includes("pequen")) return "pequena";
  if (texto.includes("median")) return "mediana";
  if (texto.includes("corporativ") || texto.includes("grande")) return "corporativo";
  return TAMANO_SI_SE_DESCONOCE;
}
