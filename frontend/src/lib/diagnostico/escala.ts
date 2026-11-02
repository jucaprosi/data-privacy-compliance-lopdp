/**
 * Escala de madurez SMARTCIDI en la pantalla (DIAG-09): única copia en el frontend.
 *
 * Los textos son los de governance/contratos/escala_madurez.json (hojas «Niveles de Madurez» y
 * «Catálogos» del archivo de assessment). El estado de cumplimiento NO se elige: lo deriva el
 * servidor del nivel asignado (DIAG-08 R3); `estadoDerivado` solo lo anticipa mientras llega la
 * respuesta del servidor, que es la que manda.
 */
export interface NivelAsignado {
  nivel: number;
  nombre: string;
  /** Primera parte del nombre, para el botón. */
  corto: string;
  criterio: string;
}

export interface EscalonEvidencia {
  nivel: number;
  nombre: string;
  /** Primera parte del nombre, para el botón. */
  corto: string;
  detalle: string;
}

export const NIVELES_ASIGNADOS: readonly NivelAsignado[] = [
  { nivel: 1, nombre: "Inicial / Reactivo", corto: "Inicial", criterio: "No existe o se gestiona informalmente" },
  { nivel: 2, nombre: "Básico / Repetible", corto: "Básico", criterio: "Prácticas aisladas o documentos iniciales" },
  {
    nivel: 3,
    nombre: "Definido / Documentado",
    corto: "Definido",
    criterio: "Políticas, matrices, procedimientos y responsables definidos",
  },
  {
    nivel: 4,
    nombre: "Gestionado / Demostrable",
    corto: "Gestionado",
    criterio: "Se aplica, se revisa, tiene seguimiento y métricas",
  },
  {
    nivel: 5,
    nombre: "Optimizado / Mejora continua",
    corto: "Optimizado",
    criterio: "Integrado a gobierno, riesgos y seguridad, con mejora demostrable",
  },
];

export const ESCALONES_EVIDENCIA: readonly EscalonEvidencia[] = [
  { nivel: 0, nombre: "Verbal: sin evidencia", corto: "Verbal", detalle: "sin evidencia" },
  { nivel: 1, nombre: "Informal: correo, captura, práctica no formalizada", corto: "Informal", detalle: "correo, captura, práctica no formalizada" },
  { nivel: 2, nombre: "Documental: política, matriz, procedimiento, contrato", corto: "Documental", detalle: "política, matriz, procedimiento, contrato" },
  { nivel: 3, nombre: "Operativa: registros de aplicación", corto: "Operativa", detalle: "registros de aplicación" },
  { nivel: 4, nombre: "Revisada: auditada o revisada por la dirección", corto: "Revisada", detalle: "auditada o revisada por la dirección" },
];

export const NIVEL_EVIDENCIA_MAXIMO = ESCALONES_EVIDENCIA[ESCALONES_EVIDENCIA.length - 1].nivel;

export function nivelAsignadoDe(nivel: number | null | undefined): NivelAsignado | undefined {
  return NIVELES_ASIGNADOS.find((n) => n.nivel === nivel);
}

export function escalonEvidenciaDe(nivel: number): EscalonEvidencia | undefined {
  return ESCALONES_EVIDENCIA.find((e) => e.nivel === nivel);
}

export type EstadoDerivado = "Conforme" | "Parcial" | "No Conforme" | "Pendiente";

/** DIAG-08 R3: 1 ⇒ No Conforme; 2–3 ⇒ Parcial; 4–5 ⇒ Conforme; sin nivel ⇒ Pendiente. */
export function estadoDerivado(nivel: number | null | undefined): EstadoDerivado {
  if (nivel == null) return "Pendiente";
  if (nivel <= 1) return "No Conforme";
  if (nivel <= 3) return "Parcial";
  return "Conforme";
}

/** Convierte la evidencia sellada con la escala anterior (E0–E3) a los cinco escalones. */
export function evidenciaDesdeEscalaAnterior(nivel: number): number {
  return nivel <= 0 ? 0 : nivel + 1;
}

/** Rango de niveles que corresponde a un estado (DIAG-08 R3): 1, 2–3 o 4–5. */
export function rangoDeEstado(estado: EstadoDerivado): { desde: number; hasta: number } | null {
  if (estado === "Conforme") return { desde: 4, hasta: 5 };
  if (estado === "Parcial") return { desde: 2, hasta: 3 };
  if (estado === "No Conforme") return { desde: 1, hasta: 1 };
  return null;
}

/** Primer nivel del rango de un estado. Solo para pruebas: la pantalla nunca lo aplica por defecto. */
export function nivelMinimoDeEstado(estado: EstadoDerivado): number | null {
  return rangoDeEstado(estado)?.desde ?? null;
}
