"use server";

export interface RespuestaScoringInput {
  // Soporte universal para formatos del cliente (Zustand, API y Forms)
  idPregunta?: string | number;
  id_pregunta?: string | number;
  preguntaId?: number | string;

  // Estado de conformidad (booleano o enum)
  conforme?: boolean;
  respuesta_afirmativa?: boolean;
  cumple?: "Conforme" | "Parcial" | "No Conforme" | "Pendiente" | string;

  // Criticidad
  esCritica?: boolean;
  es_nucleo?: boolean;

  // Nivel de soporte documental (número 0..3 o cadena E0..E3)
  evidenciaNivel?: number | string;
  nivelEvidencia?: "E0" | "E1" | "E2" | "E3" | string;
  nivel_evidencia?: "E0" | "E1" | "E2" | "E3" | string;

  // Ponderación de riesgo
  riesgoBase?: number;
}

export interface MetricasDashboardResponse {
  // 1. Conformidad Legal Booleana (Doctrina 4)
  conformidadLegalBooleana: boolean;
  conformidadBooleana: boolean; // Alias interoperable con Zustand
  estadoConformidad: "Conforme (Sin Brechas Críticas)" | "No Conforme (Brecha Jurídica Crítica)";
  conformidadEtiqueta: string; // Alias interoperable con Zustand

  // 2. Nivel de Madurez SPDP (0 al 3) con Bloqueo Jerárquico
  madurezNivel: 0 | 1 | 2 | 3;
  madurezSPDP: number; // Alias interoperable con Zustand (0.00 a 3.00)
  madurezEtiqueta: string;
  madurezNivelEtiqueta: string; // Alias interoperable con Zustand
  madurezPromedioFlotante: number;
  bloqueoJerarquicoActivado: boolean;
  motivoBloqueo?: string;

  // 3. Cobertura de Evidencias (E0 a E3)
  calidadEvidencias: number; // Alias interoperable con Zustand (0.00 a 3.00)
  calidadEvidenciasEtiqueta: string; // "E0.0", "E2.5", etc.
  coberturaEvidenciasPromedio: number; // Promedio flotante exacto (0.0 a 3.0)
  coberturaEvidenciasPorcentaje: number; // Porcentaje relativo (0% a 100%)
  desgloseEvidencias: {
    E0: number;
    E1: number;
    E2: number;
    E3: number;
  };

  // 4. Riesgo Residual
  riesgoResidual: number; // Porcentaje de riesgo no mitigado (0% a 100%)
  riesgoResidualPorcentaje: number; // Alias interoperable con Zustand
  riesgoInherenteBase: number;
  reduccionRiesgoTotal: number;

  // Metadatos de auditoría
  porcentajeConformidad: number;
  totalPreguntas: number;
  totalRespondidas: number; // Alias interoperable con Zustand
  brechasCriticasAbiertas: number;
  preguntasConformes: number;
}

export interface ServerActionResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * Server Action: Computa las métricas de Scoring Multidimensional Cuádruple
 * bajo estricta subordinación a la Doctrina 4 del PRD (Sin promedios engañosos y con bloqueo jerárquico).
 * Totalmente compatible con useAuditStore, CentralDashboard y DiagnosticCanvas.
 */
export async function calcularMetricasDashboard(
  respuestasClient: RespuestaScoringInput[]
): Promise<ServerActionResponse<MetricasDashboardResponse>> {
  try {
    if (!Array.isArray(respuestasClient) || respuestasClient.length === 0) {
      return {
        success: false,
        error: "El arreglo de respuestas no puede estar vacío.",
        data: {
          conformidadLegalBooleana: false,
          conformidadBooleana: false,
          estadoConformidad: "No Conforme (Brecha Jurídica Crítica)",
          conformidadEtiqueta: "No Conforme (Brecha Jurídica Crítica)",
          madurezNivel: 0,
          madurezSPDP: 0,
          madurezEtiqueta: "0 (Caótico)",
          madurezNivelEtiqueta: "0 (Caótico)",
          madurezPromedioFlotante: 0.0,
          bloqueoJerarquicoActivado: false,
          calidadEvidencias: 0,
          calidadEvidenciasEtiqueta: "E0.0",
          coberturaEvidenciasPromedio: 0.0,
          coberturaEvidenciasPorcentaje: 0.0,
          desgloseEvidencias: { E0: 0, E1: 0, E2: 0, E3: 0 },
          riesgoResidual: 100,
          riesgoResidualPorcentaje: 100,
          riesgoInherenteBase: 100,
          reduccionRiesgoTotal: 0,
          porcentajeConformidad: 0,
          totalPreguntas: 0,
          totalRespondidas: 0,
          brechasCriticasAbiertas: 0,
          preguntasConformes: 0,
        },
      };
    }

    // Filtrar aquellas que no estén "Pendiente"
    const activas = respuestasClient.filter((r) => r.cumple !== "Pendiente");
    const total = activas.length > 0 ? activas.length : respuestasClient.length;
    const coleccion = activas.length > 0 ? activas : respuestasClient;

    let conformesCount = 0;
    let puntosMadurez = 0;
    let sumaPonderadaEvidencias = 0;
    let mitigacionAcumulada = 0;
    let puntosConformidad = 0;

    const desgloseEvidencias = { E0: 0, E1: 0, E2: 0, E3: 0 };
    const brechasCriticas: RespuestaScoringInput[] = [];

    for (const r of coleccion) {
      // Normalización de conformidad
      const esConforme =
        r.conforme === true ||
        r.respuesta_afirmativa === true ||
        r.cumple === "Conforme" ||
        r.cumple === "Parcial";

      const esCritica = r.esCritica ?? r.es_nucleo ?? true;

      const esNoConforme =
        r.cumple === "No Conforme" ||
        r.conforme === false ||
        r.respuesta_afirmativa === false;

      // Normalización de nivel de evidencia
      let nivelKey: "E0" | "E1" | "E2" | "E3" = "E0";
      let pesoEvidencia = 0;
      let porcentajeMitigacion = 0;

      const rawNum = typeof r.evidenciaNivel === "number" ? r.evidenciaNivel : undefined;
      const rawStr = String(
        r.nivelEvidencia ?? r.nivel_evidencia ?? r.evidenciaNivel ?? "E0"
      ).toUpperCase();

      if (rawNum === 3 || rawStr.includes("E3") || rawStr.includes("PROBADA")) {
        nivelKey = "E3";
        pesoEvidencia = 3;
        porcentajeMitigacion = 0.95;
      } else if (rawNum === 2 || rawStr.includes("E2") || rawStr.includes("IMPLEMENTADA")) {
        nivelKey = "E2";
        pesoEvidencia = 2;
        porcentajeMitigacion = 0.7;
      } else if (rawNum === 1 || rawStr.includes("E1") || rawStr.includes("DOCUMENTADA")) {
        nivelKey = "E1";
        pesoEvidencia = 1;
        porcentajeMitigacion = 0.4;
      } else {
        nivelKey = "E0";
        pesoEvidencia = 0;
        porcentajeMitigacion = 0.0;
      }

      desgloseEvidencias[nivelKey]++;
      sumaPonderadaEvidencias += pesoEvidencia;

      if (esConforme) {
        conformesCount++;
        const factorParcial = r.cumple === "Parcial" ? 0.5 : 1.0;
        puntosConformidad += factorParcial;
        puntosMadurez += (pesoEvidencia > 0 ? pesoEvidencia : 0.5) * factorParcial;
        mitigacionAcumulada += porcentajeMitigacion * factorParcial;
      } else if (esNoConforme) {
        if (esCritica) {
          brechasCriticas.push(r);
        }
      }
    }

    // --- 1. CONFORMIDAD LEGAL BOOLEANA (Doctrina 4) ---
    // Si existe tan solo UNA respuesta No Conforme en pregunta crítica, el veredicto es estricto
    const conformidadLegalBooleana = brechasCriticas.length === 0;
    const estadoConformidad = conformidadLegalBooleana
      ? "Conforme (Sin Brechas Críticas)"
      : "No Conforme (Brecha Jurídica Crítica)";

    // --- 2. NIVEL DE MADUREZ SPDP CON BLOQUEO JERÁRQUICO ---
    const madurezPromedio = Number((puntosMadurez / total).toFixed(2));
    let madurezNivel: 0 | 1 | 2 | 3 = 0;
    let madurezEtiqueta = "0 (Caótico)";

    if (madurezPromedio >= 2.25) {
      madurezNivel = 3;
      madurezEtiqueta = "3 (Maduro explícito)";
    } else if (madurezPromedio >= 1.5) {
      madurezNivel = 2;
      madurezEtiqueta = "2 (Temprano explícito)";
    } else if (madurezPromedio >= 0.75) {
      madurezNivel = 1;
      madurezEtiqueta = "1 (Implícito)";
    } else {
      madurezNivel = 0;
      madurezEtiqueta = "0 (Caótico)";
    }

    // APLICACIÓN DEL BLOQUEO JERÁRQUICO:
    // Si hay brechas críticas abiertas, el nivel se congela forzosamente en 0 o 1
    let bloqueoJerarquicoActivado = false;
    let motivoBloqueo: string | undefined = undefined;

    if (brechasCriticas.length > 0) {
      bloqueoJerarquicoActivado = true;
      if (brechasCriticas.length >= 3) {
        madurezNivel = 0;
        madurezEtiqueta = "0 (Caótico) [Bloqueo Jerárquico por Brechas Múltiples]";
        motivoBloqueo = `Bloqueado en Nivel 0 por acumulación de ${brechasCriticas.length} brechas jurídicas críticas no compensables.`;
      } else {
        madurezNivel = Math.min(madurezNivel, 1) as 0 | 1;
        madurezEtiqueta = "1 (Implícito) [Bloqueo Jerárquico por Brecha Crítica]";
        motivoBloqueo = `Bloqueado en Nivel 1: Existe ${brechasCriticas.length} brecha jurídica crítica abierta que impide el ascenso a Nivel 2 o 3.`;
      }
    }

    // --- 3. COBERTURA DE EVIDENCIAS (E0 A E3) ---
    const coberturaEvidenciasPromedio = Number((sumaPonderadaEvidencias / total).toFixed(2));
    const coberturaEvidenciasPorcentaje = Number(
      ((coberturaEvidenciasPromedio / 3.0) * 100).toFixed(1)
    );
    const calidadEvidenciasEtiqueta = `E${coberturaEvidenciasPromedio.toFixed(1)}`;

    // --- 4. RIESGO RESIDUAL ---
    const reduccionRiesgoPromedio = (mitigacionAcumulada / total) * 100;
    const riesgoResidual = Math.max(
      0,
      Math.min(100, Math.round(100 - reduccionRiesgoPromedio))
    );

    const porcentajeConformidad = Number(((puntosConformidad / total) * 100).toFixed(1));

    const resultado: MetricasDashboardResponse = {
      // Formato estricto Server Action
      conformidadLegalBooleana,
      conformidadBooleana: conformidadLegalBooleana,
      estadoConformidad,
      conformidadEtiqueta: estadoConformidad,

      madurezNivel,
      madurezSPDP: madurezPromedio,
      madurezEtiqueta,
      madurezNivelEtiqueta: madurezEtiqueta,
      madurezPromedioFlotante: madurezPromedio,
      bloqueoJerarquicoActivado,
      motivoBloqueo,

      calidadEvidencias: coberturaEvidenciasPromedio,
      calidadEvidenciasEtiqueta,
      coberturaEvidenciasPromedio,
      coberturaEvidenciasPorcentaje,
      desgloseEvidencias,

      riesgoResidual,
      riesgoResidualPorcentaje: riesgoResidual,
      riesgoInherenteBase: 100,
      reduccionRiesgoTotal: Math.round(reduccionRiesgoPromedio),

      porcentajeConformidad,
      totalPreguntas: total,
      totalRespondidas: total,
      brechasCriticasAbiertas: brechasCriticas.length,
      preguntasConformes: conformesCount,
    };

    return {
      success: true,
      data: resultado,
    };
  } catch (error) {
    console.error("[SCORING_ACTION_ERROR]:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Error calculando métricas de scoring.",
    };
  }
}
