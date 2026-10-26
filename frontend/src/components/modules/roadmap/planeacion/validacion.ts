/**
 * Validación pura de las variables de planeación (sin React ni red).
 *
 * Refleja las restricciones de PlanningVariables del contrato: plazo de 3 a 12 meses,
 * presupuesto no negativo, moneda de tres letras, al menos un miembro del equipo y DPO.
 */
import type { PlanningVariables } from "../../../../types/roadmap";

export interface FormularioPlaneacion {
  plazo_meses: string;
  presupuesto: string;
  moneda: string;
  equipo: string;
  dpo: string;
  idioma: "ES" | "EN";
  sistemas_proveedores: string;
  contratos_relevantes: string;
  prioridades_negocio: string;
  restricciones_locales: string;
  evidencia_por_control: Record<string, boolean>;
}

export type ErroresPlaneacion = Partial<Record<keyof FormularioPlaneacion, string>>;

export const PLAZO_MIN_MESES = 3;
export const PLAZO_MAX_MESES = 12;
export const TOTAL_CONTROLES = 80;

/** Controles P1 a P80 del catálogo. */
export const CONTROLES: readonly string[] = Array.from({ length: TOTAL_CONTROLES }, (_, i) => `P${i + 1}`);

export function formularioInicial(): FormularioPlaneacion {
  return {
    plazo_meses: "6",
    presupuesto: "",
    moneda: "USD",
    equipo: "",
    dpo: "",
    idioma: "ES",
    sistemas_proveedores: "",
    contratos_relevantes: "",
    prioridades_negocio: "",
    restricciones_locales: "",
    evidencia_por_control: {},
  };
}

/** Una entrada por línea; descarta vacíos y repetidos. */
export function lineas(texto: string): string[] {
  const vistas = new Set<string>();
  for (const bruta of texto.split(/\r?\n/)) {
    const limpia = bruta.trim();
    if (limpia) vistas.add(limpia);
  }
  return [...vistas];
}

export function validar(form: FormularioPlaneacion): ErroresPlaneacion {
  const errores: ErroresPlaneacion = {};

  const plazo = Number(form.plazo_meses);
  if (form.plazo_meses.trim() === "" || !Number.isInteger(plazo)) {
    errores.plazo_meses = "Indica el plazo en meses, con un número entero.";
  } else if (plazo < PLAZO_MIN_MESES || plazo > PLAZO_MAX_MESES) {
    errores.plazo_meses = `El plazo debe estar entre ${PLAZO_MIN_MESES} y ${PLAZO_MAX_MESES} meses.`;
  }

  const presupuesto = Number(form.presupuesto);
  if (form.presupuesto.trim() === "" || Number.isNaN(presupuesto)) {
    errores.presupuesto = "Indica el presupuesto disponible.";
  } else if (presupuesto < 0) {
    errores.presupuesto = "El presupuesto no puede ser negativo.";
  }

  if (!/^[A-Za-z]{3}$/.test(form.moneda.trim())) {
    errores.moneda = "La moneda debe ser un código de tres letras, por ejemplo USD.";
  }

  if (lineas(form.equipo).length === 0) {
    errores.equipo = "Indica al menos un miembro del equipo, uno por línea.";
  }

  if (form.dpo.trim() === "") {
    errores.dpo = "Indica quién ejerce como delegado de protección de datos.";
  }

  return errores;
}

/** Convierte el formulario ya validado en las variables que espera la API. */
export function aVariables(form: FormularioPlaneacion): PlanningVariables {
  const marcados: Record<string, boolean> = {};
  for (const control of CONTROLES) {
    if (form.evidencia_por_control[control]) marcados[control] = true;
  }
  return {
    plazo_meses: Number(form.plazo_meses),
    presupuesto: Number(form.presupuesto),
    moneda: form.moneda.trim().toUpperCase(),
    equipo: lineas(form.equipo),
    dpo: form.dpo.trim(),
    idioma: form.idioma,
    sistemas_proveedores: form.sistemas_proveedores.trim(),
    contratos_relevantes: form.contratos_relevantes.trim(),
    prioridades_negocio: lineas(form.prioridades_negocio),
    restricciones_locales: form.restricciones_locales.trim(),
    evidencia_por_control: marcados,
  };
}
