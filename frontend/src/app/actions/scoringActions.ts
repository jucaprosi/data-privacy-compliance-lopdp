"use server";

import { NIVEL_EVIDENCIA_MAXIMO } from "@/lib/diagnostico/escala";

/**
 * Métricas de apoyo del diagnóstico con la escala SMARTCIDI (DIAG-09).
 *
 * No calcula madurez: los niveles por dimensión los calcula el servidor (DIAG-08) y no se combinan
 * en un puntaje de la organización (INV_LOPDP_MULTIDIMENSIONAL_METRICS). Aquí solo se cuentan las
 * brechas críticas abiertas y el respaldo documental, igual que en los indicadores sellados.
 */
export interface RespuestaScoringInput {
  preguntaId?: number | string;
  /** Nivel asignado SMARTCIDI 1 a 5; sin valor la pregunta cuenta como pendiente. */
  nivelAsignado?: number | null;
  /** Escalón de evidencia 0 (verbal) a 4 (revisada). */
  evidenciaNivel?: number;
  esCritica?: boolean;
}

export interface MetricasDashboardResponse {
  conformidadLegalBooleana: boolean;
  estadoConformidad: "Conforme (Sin Brechas Críticas)" | "No Conforme (Brecha Jurídica Crítica)";
  /** Media del escalón de evidencia sobre 4, en %. Describe la evidencia, no la madurez. */
  respaldoDocumental: number;
  totalRespondidas: number;
  brechasCriticasAbiertas: number;
}

export interface ServerActionResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export async function calcularMetricasDashboard(
  respuestasClient: RespuestaScoringInput[]
): Promise<ServerActionResponse<MetricasDashboardResponse>> {
  try {
    if (!Array.isArray(respuestasClient) || respuestasClient.length === 0) {
      return { success: false, error: "El arreglo de respuestas no puede estar vacío." };
    }
    const respondidas = respuestasClient.filter((r) => r.nivelAsignado != null);
    const total = respondidas.length;
    const brechasCriticasAbiertas = respondidas.filter(
      (r) => (r.esCritica ?? true) && r.nivelAsignado === 1
    ).length;
    const suma = respondidas.reduce((acc, r) => acc + (r.evidenciaNivel ?? 0), 0);
    const conforme = brechasCriticasAbiertas === 0;
    return {
      success: true,
      data: {
        conformidadLegalBooleana: conforme,
        estadoConformidad: conforme
          ? "Conforme (Sin Brechas Críticas)"
          : "No Conforme (Brecha Jurídica Crítica)",
        respaldoDocumental:
          total > 0 ? Math.round((suma / total / NIVEL_EVIDENCIA_MAXIMO) * 1000) / 10 : 0,
        totalRespondidas: total,
        brechasCriticasAbiertas,
      },
    };
  } catch (error) {
    console.error("[SCORING_ACTION_ERROR]:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Error calculando métricas de scoring.",
    };
  }
}
