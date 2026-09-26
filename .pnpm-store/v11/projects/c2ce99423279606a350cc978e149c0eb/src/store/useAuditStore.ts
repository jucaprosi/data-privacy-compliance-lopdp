import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { useState, useEffect } from "react";
import {
  DIMENSIONES_SGPDP,
  CONTROLES_ESTRUCTURALES,
  type DimensionId,
  nivelDesdeScore,
  NIVELES_MADUREZ_INDEX,
  NIVEL_TOPE_BRECHA_ESTRUCTURAL,
  UMBRAL_DEGRADACION_ESTRUCTURAL,
  CRITICIDAD_BLOQUEANTE,
  CRITICIDAD_EVIDENCIA_EXIGIBLE,
  UMBRAL_EVIDENCIA_EXIGIBLE,
  NIVEL_TOPE_EVIDENCIA_INSUFICIENTE,
  COBERTURA_MINIMA_EMISION,
  RIESGO_BRECHA_CRITICA,
  RIESGO_BRECHA_ALTA,
} from "@/lib/dimensionesSGPDP";
import { RESPUESTAS_REFERENCIA } from "@/lib/assessmentReferencia";
import {
  BANCO_PREGUNTAS,
  aplicaATamano,
  normalizarTamano,
} from "@/lib/bancoPreguntas";
import type { InstantaneaProyecto, ProyectoGuardado } from "@/lib/proyectos";
import { NORMATIVAS, NORMATIVA_POR_DEFECTO, type NormativaId } from "@/lib/normativas";
import {
  correlativoDeCodigo,
  esEvidenciaValida,
  type EvidenciaDocumental,
  type ModoEvidencia,
  type NuevaEvidencia,
} from "@/lib/evidencias/tipos";
import type {
  DecisionPropuesta,
  PropuestaIA,
  RastroPreanalisis,
} from "@/lib/preanalisis/tipos";
import { limpiarArchivosSesion, olvidarArchivo } from "@/lib/preanalisis/archivosSesion";

export type NormativaAuditoria = NormativaId | null;

export interface CompanyData {
  razonSocial: string;
  sector: string;
  tamano: string;
}

export type ActiveView =
  | "configuracion"
  | "dashboard"
  | "diagnostico"
  | "ia_chat"
  | "rat"
  | "riesgos"
  | "dpo"
  | "auditoria"
  | "evidencias"
  | "incidentes"
  | "arco"
  | "mtge_relacional"
  | "terceros"
  | "mitigacion_ia"
  | "reportes"
  | "niif_ingesta"
  | "niif_reclasificacion"
  | "niif_subtotales"
  | "niif_mpm"
  | "niif_diagnostico"
  | "niif_exportacion"
  | "niif_doctrina";

export type ThemeMode = "dark" | "light";

export type EstadoCumplimiento = "Conforme" | "Parcial" | "No Conforme" | "Pendiente";

export interface RespuestaItemStore {
  preguntaId: number;
  cumple: EstadoCumplimiento;
  evidenciaNivel: number; // 0 (E0), 1 (E1), 2 (E2), 3 (E3)
  esCritica: boolean;
  riesgoBase: number; // 1 a 10
  pendienteValidacion?: boolean;
  dimensionId?: DimensionId;
  criticidad?: number; // 1 a 5, pondera el riesgo del control
  control?: string;
  // Marca las respuestas del conjunto de referencia. Pueblan el tablero pero
  // carecen de valor probatorio: no pueden sellarse en un snapshot de auditoría.
  esReferencia?: boolean;
  // Presente solo cuando el auditor aceptó o editó una propuesta de la IA: deja
  // constancia de qué documento y qué modelo la originaron.
  preanalisis?: RastroPreanalisis;
}

export type SeveridadBrecha = "Crítico" | "Alto" | "Medio";

export interface BrechaDetectada {
  preguntaId: number;
  control: string;
  dimensionId: DimensionId;
  dimensionNombre: string;
  severidad: SeveridadBrecha;
  nivelEfectivo: number;
  riesgo: number;
  esEstructural: boolean;
}

export interface ResultadoDimension {
  id: DimensionId;
  nombre: string;
  peso: number;
  itemsAplicables: number;
  itemsEvaluados: number;
  coberturaPorcentaje: number;
  score: number; // 0 a 100
  nivel: number; // 1 a 5
  nivelEtiqueta: string;
  brechasCriticas: number;
  brechasAltas: number;
  observacion: string;
}

export interface ResultadoAssessment {
  scorePonderado: number; // 0 a 100
  nivelTeorico: number;
  nivelTeoricoEtiqueta: string;
  nivelAjustado: number;
  nivelAjustadoEtiqueta: string;
  ajustePorBrechaEstructural: boolean;
  // El nivel global quedó topado en 3 por controles de alta criticidad sin
  // evidencia suficiente, aunque el score ponderado diera para más.
  ajustePorEvidenciaInsuficiente: boolean;
  // La cobertura no alcanza el mínimo de emisión: el resultado no califica.
  coberturaInsuficiente: boolean;
  dimensiones: ResultadoDimension[];
  brechas: BrechaDetectada[];
  brechasCriticas: number;
  brechasAltas: number;
  controlesEstructuralesDegradados: number;
  /** Controles bloqueantes (criticidad 5) con nivel efectivo por debajo de 3. */
  controlesBloqueantesDegradados: number;
  /** Controles de criticidad alta cuya evidencia no llega al mínimo exigible. */
  controlesSinEvidenciaSuficiente: number;
  controlesEstructuralesEvaluados: number[];
  totalEvaluados: number;
  totalAplicables: number;
  coberturaPorcentaje: number;
  // El tablero se está alimentando únicamente del conjunto de referencia: hay
  // resultados que mirar, pero ninguno proviene de un diagnóstico real.
  soloReferencia: boolean;
  respuestasPropias: number;
  // Modo con que se calculó: en "verificado" el nivel de evidencia de un
  // control sin documento vinculado cuenta como E0.
  modo: ModoEvidencia;
  controlesConEvidenciaVinculada: number;
}

export interface ScoringMultidimensional {
  conformidadBooleana: boolean;
  conformidadEtiqueta: string; // "Conforme" o "No Conforme (Brecha Crítica)"
  porcentajeConformidad: number;
  calidadEvidencias: number; // 0.00 a 3.00
  calidadEvidenciasEtiqueta: string;
  madurezSPDP: number; // 0.00 a 3.00
  madurezNivelEtiqueta: string;
  riesgoResidualPorcentaje: number;
  brechasCriticasAbiertas: number;
  totalRespondidas: number;
  bloqueoJerarquicoActivado?: boolean;
  motivoBloqueo?: string;
}

export interface CuentaNIIF {
  cuenta: string;
  descripcion: string;
  saldo_original: number;
  categoria: string;
  pl_neto: number;
}

export interface ProcesamientoResultNIIF18 {
  inferencia_columnas: {
    cuenta: string;
    descripcion: string;
    saldo: string;
    confianza_porcentaje: number;
  };
  subtotales: {
    "1_resultado_operativo": number;
    "2_resultado_antes_fin_imp": number;
    "3_resultado_periodo": number;
  };
  cuentas: CuentaNIIF[];
  diagnostico?: DiagnosticoNIIF18;
  indicadores?: IndicadoresNIIF18;
}

export interface HallazgoNIIF18 {
  codigo: string;
  severidad: "ALTA" | "MEDIA" | "BAJA" | "INFO";
  titulo: string;
  detalle: string;
  referencia: string;
  cuentas: string[];
}

export interface DiagnosticoNIIF18 {
  estado: "REQUIERE_CORRECCION" | "CON_OBSERVACIONES" | "LISTO_PARA_PRESENTAR";
  puntaje: number;
  cuadre: { diferencia: number; cuadra: boolean };
  total_cuentas: number;
  por_categoria: { categoria: string; cuentas: number; aporte: number }[];
  hallazgos: HallazgoNIIF18[];
}

export interface IndicadoresNIIF18 {
  ingresos_operativos: number;
  margen_operativo: number | null;
  margen_neto: number | null;
  tasa_efectiva_impuestos: number | null;
  cobertura_intereses: number | null;
  depreciacion_amortizacion: number;
  ebitda_referencial: number;
}

export interface RecomendacionesNIIF18 {
  acciones: { prioridad: "P1" | "P2" | "P3"; tipo: string; accion: string; fundamento: string; hallazgo: string | null; cuentas: string[] }[];
  hoja_de_ruta: { fase: string; descripcion: string; referencia: string }[];
}

export interface MpmRecord {
  nombre: string;
  subtotal_base: string;
  valor_base: number;
  ajuste: number;
  efecto_fiscal: number;
  total_mpm: number;
  justificacion: string;
}

export interface AuditStoreState {
  companyData: CompanyData;
  normativaSeleccionada: NormativaAuditoria;
  archivosCargados: File[];
  isConfigured: boolean;
  
  // NIIF 18
  niif18Data: ProcesamientoResultNIIF18 | null;
  setNiif18Data: (data: ProcesamientoResultNIIF18 | null) => void;
  mpmRecords: MpmRecord[];
  setMpmRecords: (records: MpmRecord[]) => void;
  doctrinaData: Record<string, string> | null;
  setDoctrinaData: (data: Record<string, string> | null) => void;

  activeView: ActiveView;
  isCommandPaletteOpen: boolean;
  hasHydrated: boolean;

  // Diagnóstico Activo (Assessment Adaptativo)
  respuestas: RespuestaItemStore[];
  preguntaActualIndex: number;
  timeboxRestante: number; // segundos (default 3600 = 60 min)

  theme: ThemeMode;
  setCompanyData: (data: Partial<CompanyData>) => void;
  setNormativa: (normativa: NormativaAuditoria) => void;
  addArchivos: (nuevos: File[]) => void;
  removeArchivo: (index: number) => void;
  setIsConfigured: (isConfigured: boolean) => void;
  setActiveView: (view: ActiveView) => void;
  setCommandPaletteOpen: (open: boolean) => void;
  toggleCommandPalette: () => void;
  setHasHydrated: (hasHydrated: boolean) => void;
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;

  // Acciones de Diagnóstico
  setRespuesta: (preguntaId: number, data: Partial<RespuestaItemStore>) => void;
  setPreguntaActualIndex: (index: number) => void;
  setTimeboxRestante: (segundos: number | ((prev: number) => number)) => void;
  calcularScoring: () => ScoringMultidimensional;
  calcularResultadoAssessment: (modo?: ModoEvidencia) => ResultadoAssessment;

  // Evidencias documentales (huella SHA-256 vinculada a controles)
  evidencias: EvidenciaDocumental[];
  /** Último correlativo EVD asignado en el proyecto; nunca retrocede. */
  correlativoEvidencias: number;
  /** Registra una evidencia; si la misma huella ya existe devuelve la existente. */
  registrarEvidencia: (nueva: NuevaEvidencia) => EvidenciaDocumental;
  vincularEvidencia: (evidenciaId: string, preguntaId: number) => void;
  desvincularEvidencia: (evidenciaId: string, preguntaId: number) => void;
  eliminarEvidencia: (evidenciaId: string) => void;
  evidenciasDeControl: (preguntaId: number) => EvidenciaDocumental[];

  // Propuestas del pre-llenado asistido (una vigente por control)
  propuestasIA: Record<number, PropuestaIA>;
  guardarPropuestaIA: (propuesta: PropuestaIA) => void;
  decidirPropuestaIA: (preguntaId: number, decision: DecisionPropuesta) => void;
  reiniciarDiagnostico: () => void;

  resetConfig: () => void;

  // Gestión de proyectos (menú Archivo)
  proyectoActivo: ProyectoActivo | null;
  cambiosSinGuardar: boolean;
  obtenerInstantanea: () => InstantaneaProyecto;
  cargarProyecto: (proyecto: ProyectoGuardado) => void;
  nuevoProyecto: () => void;
  marcarGuardado: (proyecto: ProyectoActivo) => void;
}

export interface ProyectoActivo {
  id: string;
  nombre: string;
}

export const useAuditStore = create<AuditStoreState>()(
  persist(
    (set, get) => ({
      companyData: {
        razonSocial: "Corporación Demo LOPDP 360",
        sector: "Telecomunicaciones y Tecnología",
        tamano: "Mediana Empresa (50-199)",
      },
      normativaSeleccionada: null,
      archivosCargados: [],
      isConfigured: false,
      evidencias: [],
      correlativoEvidencias: 0,
      propuestasIA: {},

      // NIIF 18
      niif18Data: null,
      setNiif18Data: (data) => set({ niif18Data: data }),
      mpmRecords: [],
      setMpmRecords: (records) => set({ mpmRecords: records }),
      doctrinaData: null,
      setDoctrinaData: (data) => set({ doctrinaData: data }),

      activeView: "configuracion",
      isCommandPaletteOpen: false,
      hasHydrated: false,
      theme: "dark",

      respuestas: RESPUESTAS_REFERENCIA,
      preguntaActualIndex: 0,
      timeboxRestante: 3540,

      proyectoActivo: null,
      cambiosSinGuardar: false,

      setTheme: (theme) => set({ theme }),
      toggleTheme: () => set((state) => ({ theme: state.theme === "dark" ? "light" : "dark" })),

      setCompanyData: (data) =>
        set((state) => ({
          companyData: { ...state.companyData, ...data },
          cambiosSinGuardar: true,
        })),

      // Doctrina 10 del PRD: Purga Transaccional ante el cambio de normativa
      setNormativa: (normativa) => {
        const anterior = get().normativaSeleccionada;
        set((state) => {
          const cambioNorma = state.normativaSeleccionada !== normativa;
          // La evidencia de un régimen no puede respaldar controles de otro:
          // el cambio de normativa purga también el registro de evidencias.
          return {
            normativaSeleccionada: normativa,
            archivosCargados: cambioNorma ? [] : state.archivosCargados,
            evidencias: cambioNorma ? [] : state.evidencias,
            propuestasIA: cambioNorma ? {} : state.propuestasIA,
            cambiosSinGuardar: state.cambiosSinGuardar || cambioNorma,
          };
        });
        // Los archivos recordados para el análisis son contenido del cliente: no
        // sobreviven a la purga de evidencias.
        if (get().normativaSeleccionada !== anterior) limpiarArchivosSesion();
      },

      addArchivos: (nuevos) =>
        set((state) => ({
          archivosCargados: [...state.archivosCargados, ...nuevos],
        })),

      removeArchivo: (index) =>
        set((state) => ({
          archivosCargados: state.archivosCargados.filter((_, i) => i !== index),
        })),

      setIsConfigured: (isConfigured) =>
        set((state) => ({
          isConfigured,
          cambiosSinGuardar:
            state.cambiosSinGuardar || state.isConfigured !== isConfigured,
        })),

      setActiveView: (activeView) => set({ activeView }),

      setCommandPaletteOpen: (isCommandPaletteOpen) => set({ isCommandPaletteOpen }),

      toggleCommandPalette: () =>
        set((state) => ({ isCommandPaletteOpen: !state.isCommandPaletteOpen })),

      setHasHydrated: (hasHydrated) => set({ hasHydrated }),

      // Acciones de Diagnóstico
      setRespuesta: (preguntaId, data) =>
        set((state) => {
          // La primera respuesta propia del auditor descarta el conjunto de
          // referencia: mezclar declaraciones reales con respuestas sintéticas
          // produciría un resultado que no describe a ninguna organización.
          const base = state.respuestas.some((r) => r.esReferencia)
            ? state.respuestas.filter((r) => !r.esReferencia)
            : state.respuestas;
          const index = base.findIndex((r) => r.preguntaId === preguntaId);
          if (index >= 0) {
            const copia = [...base];
            const previa = copia[index];
            // Una respuesta contestada por el auditor deja de ser referencia, y
            // su criticidad se realinea con la del banco para que el riesgo no
            // se calcule contra una ponderación heredada de la semilla.
            const criticidad =
              data.criticidad ??
              (data.esCritica !== undefined && data.esCritica !== previa.esCritica
                ? data.esCritica
                  ? 5
                  : 3
                : previa.criticidad);
            copia[index] = {
              ...previa,
              ...data,
              criticidad,
              esReferencia: false,
            };
            return { respuestas: copia, cambiosSinGuardar: true };
          }
          const nueva: RespuestaItemStore = {
            preguntaId,
            cumple: data.cumple || "Pendiente",
            evidenciaNivel: data.evidenciaNivel ?? 0,
            esCritica: data.esCritica ?? false,
            riesgoBase: data.riesgoBase ?? 5,
            pendienteValidacion: data.pendienteValidacion ?? false,
            ...data,
            esReferencia: false,
          };
          return { respuestas: [...base, nueva], cambiosSinGuardar: true };
        }),

      setPreguntaActualIndex: (preguntaActualIndex) => set({ preguntaActualIndex }),

      setTimeboxRestante: (val) =>
        set((state) => ({
          timeboxRestante:
            typeof val === "function" ? val(state.timeboxRestante) : val,
        })),

      calcularScoring: () => {
        const { respuestas } = get();
        const respondidas = respuestas.filter((r) => r.cumple !== "Pendiente");
        const total = respondidas.length;

        if (total === 0) {
          return {
            conformidadBooleana: true,
            conformidadEtiqueta: "Sin Evaluar",
            porcentajeConformidad: 100,
            calidadEvidencias: 0,
            calidadEvidenciasEtiqueta: "E0 (Sin evaluar)",
            madurezSPDP: 0,
            madurezNivelEtiqueta: "Nivel 0 · Inexistente",
            riesgoResidualPorcentaje: 0,
            brechasCriticasAbiertas: 0,
            totalRespondidas: 0,
          };
        }

        // 1. Brechas críticas
        const brechasCriticas = respondidas.filter(
          (r) => r.esCritica && r.cumple === "No Conforme"
        );
        const brechasCriticasAbiertas = brechasCriticas.length;
        const tieneBrechaCritica = brechasCriticasAbiertas > 0;

        // Conformidad Legal Booleana bloqueante
        const conformidadBooleana = !tieneBrechaCritica;
        const conformidadEtiqueta = tieneBrechaCritica
          ? "No Conforme (Brecha Crítica)"
          : "Conforme";

        // Porcentaje de conformidad: Conforme = 1.0, Parcial = 0.5, No Conforme = 0.0
        const puntosConformidad = respondidas.reduce((acc, r) => {
          if (r.cumple === "Conforme") return acc + 1.0;
          if (r.cumple === "Parcial") return acc + 0.5;
          return acc;
        }, 0);
        const porcentajeConformidad =
          Math.round((puntosConformidad / total) * 1000) / 10;

        // 2. Calidad de Evidencias (E0-E3)
        const sumaEvidencias = respondidas.reduce(
          (acc, r) => acc + (r.evidenciaNivel || 0),
          0
        );
        const calidadEvidencias =
          Math.round((sumaEvidencias / total) * 100) / 100;
        const calidadEvidenciasEtiqueta = `E${calidadEvidencias.toFixed(1)}`;

        // 3. Nivel de Madurez SPDP del 0 al 3 CONDICIONADO por brechas críticas
        const factorConformidad = puntosConformidad / total;
        const factorEvidencia = calidadEvidencias / 3;
        let rawMadurez =
          Math.round((factorConformidad * 0.5 + factorEvidencia * 0.5) * 3 * 100) /
          100;

        // Teorema de no dilución de brechas: brechas críticas limitan madurez a máx 1.0
        if (tieneBrechaCritica) {
          rawMadurez = Math.min(rawMadurez, 1.0);
        }

        let madurezNivelEtiqueta = "Nivel 0 · Inexistente";
        if (rawMadurez >= 2.7) {
          madurezNivelEtiqueta = "Nivel 3 · Optimizado / Auditable";
        } else if (rawMadurez >= 2.0) {
          madurezNivelEtiqueta = "Nivel 2 · Temprano explícito";
        } else if (rawMadurez >= 1.0) {
          madurezNivelEtiqueta = "Nivel 1 · Inicial / Ad-hoc";
        }

        // 4. % de Riesgo Residual
        let riesgoTotal = 0;
        let riesgoResidual = 0;
        respondidas.forEach((r) => {
          const base = r.riesgoBase || 5;
          riesgoTotal += base;
          let factorFalla = 0;
          if (r.cumple === "No Conforme") factorFalla = 1.0;
          else if (r.cumple === "Parcial") factorFalla = 0.5;
          else factorFalla = 0.1;

          const factorEvidenciaMitigacion = 1 - (r.evidenciaNivel / 3) * 0.8;
          riesgoResidual += base * factorFalla * factorEvidenciaMitigacion;
        });

        const riesgoResidualPorcentaje =
          riesgoTotal > 0
            ? Math.min(100, Math.round((riesgoResidual / riesgoTotal) * 1000) / 10)
            : 0;

        return {
          conformidadBooleana,
          conformidadEtiqueta,
          porcentajeConformidad,
          calidadEvidencias,
          calidadEvidenciasEtiqueta,
          madurezSPDP: rawMadurez,
          madurezNivelEtiqueta,
          riesgoResidualPorcentaje,
          brechasCriticasAbiertas,
          totalRespondidas: total,
          bloqueoJerarquicoActivado: tieneBrechaCritica,
          motivoBloqueo: tieneBrechaCritica
            ? `Bloqueo Jerárquico activado por ${brechasCriticasAbiertas} brecha(s) jurídica(s) crítica(s) abierta(s)`
            : undefined,
        };
      },

      calcularResultadoAssessment: (modo = "declarado") => {
        const { respuestas, companyData, evidencias } = get();
        const controlesVerificados = new Set(
          evidencias.flatMap((e) => e.controlesVinculados)
        );

        // El tablero solo evalúa lo exigible a la talla de la organización: un
        // control podado del cuestionario no puede figurar como brecha.
        const talla = normalizarTamano(companyData.tamano);
        const exigibles = new Set(
          BANCO_PREGUNTAS.filter((p) => aplicaATamano(p, talla)).map((p) => p.id)
        );

        // Nivel asignado 1-5 derivado del estado de cumplimiento declarado.
        const nivelAsignado = (estado: EstadoCumplimiento): number => {
          if (estado === "Conforme") return 5;
          if (estado === "Parcial") return 3;
          if (estado === "No Conforme") return 1;
          return 0;
        };

        // Solo entran al cómputo los controles imputables a una dimensión. Las
        // respuestas de otros bancos (NIIF) no pertenecen a la matriz SGPDP y
        // diluirían la cobertura si se contaran.
        const delAssessment = respuestas.filter(
          (r) => r.dimensionId && exigibles.has(r.preguntaId)
        );
        const evaluadas = delAssessment.filter((r) => r.cumple !== "Pendiente");
        const idsEstructurales = new Set(
          CONTROLES_ESTRUCTURALES.map((c) => c.preguntaId)
        );

        const brechas: BrechaDetectada[] = [];
        let controlesEstructuralesDegradados = 0;
        let controlesBloqueantesDegradados = 0;
        let controlesSinEvidenciaSuficiente = 0;

        // El banco es la fuente autoritativa de dimensión y criticidad: el
        // numerador y el denominador del score tienen que caer en la misma
        // dimensión aunque la respuesta almacenada traiga otra.
        const delBanco = new Map(BANCO_PREGUNTAS.map((p) => [p.id, p]));
        const criticidadDeControl = (preguntaId: number, respaldo: number): number =>
          delBanco.get(preguntaId)?.criticidad ?? respaldo;
        const dimensionDeControl = (r: (typeof delAssessment)[number]): DimensionId =>
          delBanco.get(r.preguntaId)?.dimensionId ?? (r.dimensionId as DimensionId);

        const dimensiones: ResultadoDimension[] = DIMENSIONES_SGPDP.map((dim) => {
          const delDominio = delAssessment.filter(
            (r) => dimensionDeControl(r) === dim.id
          );
          const evaluadasDim = delDominio.filter((r) => r.cumple !== "Pendiente");

          let sumaPonderada = 0;
          let brechasCriticas = 0;
          let brechasAltas = 0;

          for (const item of evaluadasDim) {
            const asignado = nivelAsignado(item.cumple);
            // La evidencia (E0-E3) se reescala a la cota 0-4 de la matriz y
            // limita el nivel alcanzable: sin evidencia no hay madurez alta.
            const evidenciaVigente =
              modo === "verificado" && !controlesVerificados.has(item.preguntaId)
                ? 0
                : item.evidenciaNivel ?? 0;
            const evidenciaEscalada = evidenciaVigente * (4 / 3);
            const nivelEfectivo = Math.min(asignado, evidenciaEscalada + 1);

            const criticidad = criticidadDeControl(
              item.preguntaId,
              item.criticidad ?? (item.esCritica ? 5 : 3)
            );
            // El control aporta en proporción a su criticidad: un control
            // menor cumplido no compensa uno crítico incumplido.
            sumaPonderada += (nivelEfectivo / 5) * criticidad;

            const riesgo = (5 - nivelEfectivo) * criticidad;
            const esEstructural = idsEstructurales.has(item.preguntaId);

            if (esEstructural && nivelEfectivo < UMBRAL_DEGRADACION_ESTRUCTURAL) {
              controlesEstructuralesDegradados += 1;
            }
            if (
              criticidad >= CRITICIDAD_BLOQUEANTE &&
              nivelEfectivo < UMBRAL_DEGRADACION_ESTRUCTURAL
            ) {
              controlesBloqueantesDegradados += 1;
            }
            if (
              criticidad >= CRITICIDAD_EVIDENCIA_EXIGIBLE &&
              evidenciaEscalada < UMBRAL_EVIDENCIA_EXIGIBLE
            ) {
              controlesSinEvidenciaSuficiente += 1;
            }

            let severidad: SeveridadBrecha | null = null;
            if (riesgo >= RIESGO_BRECHA_CRITICA) {
              severidad = "Crítico";
              brechasCriticas += 1;
            } else if (riesgo >= RIESGO_BRECHA_ALTA) {
              severidad = "Alto";
              brechasAltas += 1;
            }

            if (severidad) {
              brechas.push({
                preguntaId: item.preguntaId,
                control: item.control ?? `Control ${item.preguntaId}`,
                dimensionId: dim.id,
                dimensionNombre: dim.nombre,
                severidad,
                nivelEfectivo: Math.round(nivelEfectivo * 100) / 100,
                riesgo: Math.round(riesgo * 10) / 10,
                esEstructural,
              });
            }
          }

          const itemsEvaluados = evaluadasDim.length;
          // El denominador es lo exigible a la talla, no lo ya respondido: de
          // otro modo una sola respuesta reportaría cobertura total.
          const aplicablesDim = BANCO_PREGUNTAS.filter(
            (p) => p.dimensionId === dim.id && exigibles.has(p.id)
          );
          const itemsAplicables = aplicablesDim.length;
          // Base ponderada: la criticidad de todo lo exigible. Lo no respondido
          // suma al denominador y no al numerador, luego computa como cero.
          const baseCriticidad = aplicablesDim.reduce(
            (acc, p) => acc + p.criticidad,
            0
          );
          const score =
            baseCriticidad > 0
              ? Math.round((sumaPonderada / baseCriticidad) * 1000) / 10
              : 0;
          const nivelInfo = nivelDesdeScore(score);
          const coberturaDim =
            itemsAplicables > 0
              ? Math.round((itemsEvaluados / itemsAplicables) * 1000) / 10
              : 0;
          // Una dimensión con cobertura insuficiente no reporta nivel bajo:
          // no reporta nivel. El dato faltante no es un hallazgo de madurez.
          const dimCalifica = coberturaDim >= COBERTURA_MINIMA_EMISION;

          let observacion = "Completar evaluación";
          if (!dimCalifica) {
            observacion = "Sin evaluación suficiente";
          } else if (brechasCriticas > 0) {
            observacion = "Dimensión estructural prioritaria";
          } else if (brechasAltas > 0) {
            observacion = "Requiere profundización";
          } else if (score >= 90) {
            observacion = "Validar trazabilidad con el inventario y el RAT";
          } else {
            observacion = "Madurez reportada; confirmar con evidencia";
          }

          return {
            id: dim.id,
            nombre: dim.nombre,
            peso: dim.peso,
            itemsAplicables,
            itemsEvaluados,
            coberturaPorcentaje: coberturaDim,
            score,
            nivel: dimCalifica ? nivelInfo.nivel : 0,
            nivelEtiqueta: dimCalifica
              ? nivelInfo.etiqueta
              : "Sin evaluación suficiente",
            brechasCriticas,
            brechasAltas,
            observacion,
          };
        });

        // Todas las dimensiones exigibles entran al ponderado con su peso
        // nominal. Renormalizar sobre lo ya evaluado inflaría el resultado de
        // un diagnóstico a medias hasta hacerlo indistinguible de uno completo.
        const dimensionesConDatos = dimensiones.filter((d) => d.itemsEvaluados > 0);
        const dimensionesExigibles = dimensiones.filter((d) => d.itemsAplicables > 0);
        const pesoTotal = dimensionesExigibles.reduce((acc, d) => acc + d.peso, 0);
        const scorePonderado =
          pesoTotal > 0
            ? Math.round(
                (dimensionesExigibles.reduce(
                  (acc, d) => acc + d.score * d.peso,
                  0
                ) /
                  pesoTotal) *
                  100
              ) / 100
            : 0;

        const coberturaPorcentaje =
          exigibles.size > 0
            ? Math.round((evaluadas.length / exigibles.size) * 1000) / 10
            : 0;
        const coberturaInsuficiente =
          coberturaPorcentaje < COBERTURA_MINIMA_EMISION;

        const nivelTeoricoInfo = nivelDesdeScore(scorePonderado);
        const ajustePorBrechaEstructural =
          controlesEstructuralesDegradados > 0 || controlesBloqueantesDegradados > 0;
        const ajustePorEvidenciaInsuficiente = controlesSinEvidenciaSuficiente > 0;
        let nivelAjustado = nivelTeoricoInfo.nivel;
        if (ajustePorBrechaEstructural) {
          nivelAjustado = Math.min(nivelAjustado, NIVEL_TOPE_BRECHA_ESTRUCTURAL);
        }
        if (ajustePorEvidenciaInsuficiente) {
          nivelAjustado = Math.min(nivelAjustado, NIVEL_TOPE_EVIDENCIA_INSUFICIENTE);
        }
        // Por debajo del mínimo de cobertura no hay nivel que emitir.
        if (coberturaInsuficiente) nivelAjustado = 0;
        const nivelAjustadoInfo =
          NIVELES_MADUREZ_INDEX[nivelAjustado] ?? nivelTeoricoInfo;

        brechas.sort((a, b) => {
          if (a.esEstructural !== b.esEstructural) return a.esEstructural ? -1 : 1;
          if (a.severidad !== b.severidad) return a.severidad === "Crítico" ? -1 : 1;
          return b.riesgo - a.riesgo;
        });

        return {
          scorePonderado,
          nivelTeorico: dimensionesConDatos.length > 0 ? nivelTeoricoInfo.nivel : 0,
          nivelTeoricoEtiqueta:
            dimensionesConDatos.length > 0
              ? nivelTeoricoInfo.etiqueta
              : "Sin evaluación suficiente",
          nivelAjustado: nivelAjustado > 0 ? nivelAjustado : 0,
          nivelAjustadoEtiqueta:
            nivelAjustado > 0
              ? nivelAjustadoInfo.etiqueta
              : "Sin evaluación suficiente",
          ajustePorBrechaEstructural,
          ajustePorEvidenciaInsuficiente,
          coberturaInsuficiente,
          dimensiones,
          brechas,
          brechasCriticas: brechas.filter((b) => b.severidad === "Crítico").length,
          brechasAltas: brechas.filter((b) => b.severidad === "Alto").length,
          controlesEstructuralesDegradados,
          controlesBloqueantesDegradados,
          controlesSinEvidenciaSuficiente,
          totalEvaluados: evaluadas.length,
          totalAplicables: exigibles.size,
          coberturaPorcentaje,
          controlesEstructuralesEvaluados: evaluadas
            .filter((r) => idsEstructurales.has(r.preguntaId))
            .map((r) => r.preguntaId),
          soloReferencia:
            evaluadas.length > 0 && evaluadas.every((r) => r.esReferencia),
          respuestasPropias: evaluadas.filter((r) => !r.esReferencia).length,
          modo,
          controlesConEvidenciaVinculada: evaluadas.filter((r) =>
            controlesVerificados.has(r.preguntaId)
          ).length,
        };
      },

      registrarEvidencia: (nueva) => {
        const { evidencias, normativaSeleccionada, correlativoEvidencias } = get();
        const normativa = normativaSeleccionada ?? NORMATIVA_POR_DEFECTO;
        const sha256 = nueva.sha256.toLowerCase();
        const existente = evidencias.find(
          (e) => e.sha256 === sha256 && e.normativa === normativa
        );
        if (existente) {
          // El mismo documento no genera otra evidencia, pero los controles
          // que se pidió vincular se incorporan a la existente.
          const pedidos = nueva.controlesVinculados ?? [];
          if (pedidos.every((c) => existente.controlesVinculados.includes(c))) {
            return existente;
          }
          const actualizada: EvidenciaDocumental = {
            ...existente,
            controlesVinculados: [...new Set([...existente.controlesVinculados, ...pedidos])],
          };
          set({
            evidencias: evidencias.map((e) => (e.id === existente.id ? actualizada : e)),
            cambiosSinGuardar: true,
          });
          return actualizada;
        }

        // El correlativo nunca retrocede: un código citado en un snapshot
        // sellado no puede reasignarse a otro documento aunque se elimine.
        const correlativo =
          Math.max(
            correlativoEvidencias,
            ...evidencias.map((e) => correlativoDeCodigo(e.codigo))
          ) + 1;
        const evidencia: EvidenciaDocumental = {
          id:
            typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
              ? crypto.randomUUID()
              : `evd-${Date.now()}-${correlativo}`,
          codigo: `EVD-${String(correlativo).padStart(4, "0")}`,
          nombreArchivo: nueva.nombreArchivo,
          tamanoBytes: nueva.tamanoBytes,
          tipoMime: nueva.tipoMime,
          sha256,
          normativa,
          controlesVinculados: [...new Set(nueva.controlesVinculados ?? [])],
          registradaEn: new Date().toISOString(),
        };
        set({
          evidencias: [...evidencias, evidencia],
          correlativoEvidencias: correlativo,
          cambiosSinGuardar: true,
        });
        return evidencia;
      },

      vincularEvidencia: (evidenciaId, preguntaId) =>
        set((state) => ({
          evidencias: state.evidencias.map((e) =>
            e.id === evidenciaId && !e.controlesVinculados.includes(preguntaId)
              ? { ...e, controlesVinculados: [...e.controlesVinculados, preguntaId] }
              : e
          ),
          cambiosSinGuardar: true,
        })),

      desvincularEvidencia: (evidenciaId, preguntaId) =>
        set((state) => ({
          evidencias: state.evidencias.map((e) =>
            e.id === evidenciaId
              ? {
                  ...e,
                  controlesVinculados: e.controlesVinculados.filter((c) => c !== preguntaId),
                }
              : e
          ),
          cambiosSinGuardar: true,
        })),

      eliminarEvidencia: (evidenciaId) => {
        const eliminada = get().evidencias.find((e) => e.id === evidenciaId);
        set((state) => ({
          evidencias: state.evidencias.filter((e) => e.id !== evidenciaId),
          // Una propuesta apoyada en un documento eliminado deja de tener sustento.
          propuestasIA: Object.fromEntries(
            Object.entries(state.propuestasIA).filter(([, p]) => p.evidenciaId !== evidenciaId)
          ),
          cambiosSinGuardar: true,
        }));
        if (eliminada) olvidarArchivo(eliminada.sha256);
      },

      evidenciasDeControl: (preguntaId) =>
        get().evidencias.filter((e) => e.controlesVinculados.includes(preguntaId)),

      guardarPropuestaIA: (propuesta) =>
        set((state) => {
          // El análisis es asíncrono: si el documento se eliminó o la normativa
          // cambió (lo que purga las evidencias) mientras tanto, la propuesta
          // quedaría sin sustento y se descarta.
          if (!state.evidencias.some((e) => e.id === propuesta.evidenciaId)) return {};
          return {
            propuestasIA: { ...state.propuestasIA, [propuesta.preguntaId]: propuesta },
          };
        }),

      decidirPropuestaIA: (preguntaId, decision) =>
        set((state) => {
          const propuesta = state.propuestasIA[preguntaId];
          if (!propuesta) return {};
          return {
            propuestasIA: {
              ...state.propuestasIA,
              [preguntaId]: { ...propuesta, decision, decididaEn: new Date().toISOString() },
            },
            cambiosSinGuardar: true,
          };
        }),

      reiniciarDiagnostico: () =>
        set({
          respuestas: [],
          preguntaActualIndex: 0,
          timeboxRestante: 3600,
          cambiosSinGuardar: true,
        }),

      obtenerInstantanea: () => {
        const s = get();
        return {
          companyData: s.companyData,
          normativaSeleccionada: s.normativaSeleccionada,
          isConfigured: s.isConfigured,
          respuestas: s.respuestas,
          preguntaActualIndex: s.preguntaActualIndex,
          timeboxRestante: s.timeboxRestante,
          evidencias: s.evidencias,
          correlativoEvidencias: s.correlativoEvidencias,
        };
      },

      cargarProyecto: (proyecto) => {
        const guardada = proyecto.datos.normativaSeleccionada;
        const normativa: NormativaId =
          guardada && guardada in NORMATIVAS ? guardada : NORMATIVA_POR_DEFECTO;
        // El proyecto proviene del almacenamiento del navegador: se descartan
        // las evidencias mal formadas o de otra normativa (Doctrina 10). Los
        // proyectos anteriores al registro de evidencias no traen el campo.
        const evidencias = (proyecto.datos.evidencias ?? []).filter(
          (e): e is EvidenciaDocumental => esEvidenciaValida(e) && e.normativa === normativa
        );
        set({
          ...proyecto.datos,
          evidencias,
          // Las propuestas de la IA contienen citas (texto del documento) y no se
          // guardan con el proyecto: solo perdura el rastro en cada respuesta.
          propuestasIA: {},
          correlativoEvidencias: Math.max(
            proyecto.datos.correlativoEvidencias ?? 0,
            ...evidencias.map((e) => correlativoDeCodigo(e.codigo))
          ),
          normativaSeleccionada: normativa,
          // Los archivos cargados no forman parte de la instantánea (File[] no
          // es serializable) y pertenecen al proyecto anterior: se purgan.
          archivosCargados: [],
          activeView: "dashboard",
          proyectoActivo: { id: proyecto.id, nombre: proyecto.nombre },
          cambiosSinGuardar: false,
        });
        limpiarArchivosSesion();
      },

      nuevoProyecto: () => {
        get().resetConfig();
        set({ proyectoActivo: null, cambiosSinGuardar: false });
        limpiarArchivosSesion();
      },

      marcarGuardado: (proyecto) =>
        set({ proyectoActivo: proyecto, cambiosSinGuardar: false }),

      resetConfig: () =>
        set({
          companyData: {
            razonSocial: "",
            sector: "Telecomunicaciones y Tecnología",
            tamano: "Microempresa (1-9)",
          },
          normativaSeleccionada: null,
          archivosCargados: [],
          evidencias: [],
          correlativoEvidencias: 0,
          propuestasIA: {},
          isConfigured: false,
          activeView: "configuracion",
          isCommandPaletteOpen: false,
          hasHydrated: true,
          respuestas: [],
          preguntaActualIndex: 0,
          timeboxRestante: 3600,
        }),
    }),
    {
      name: "jubys-audit-storage",
      storage: createJSONStorage(() => localStorage),
      version: 4,
      migrate: (persisted: unknown, version: number) => {
        const estado = persisted as Partial<AuditStoreState> | undefined;
        if (!estado) return estado;
        let migrado: Partial<AuditStoreState> = { ...estado };
        // v2: las respuestas previas carecen de dimensionId y no pueden
        // imputarse a ninguna dimensión; se reemplazan por la referencia.
        if (version < 2) {
          migrado = { ...migrado, respuestas: RESPUESTAS_REFERENCIA };
        }
        // v3: el assessment de protección de datos se ejecutaba bajo las
        // etiquetas PI e ISO, que ahora no están disponibles; pasa a LOPDP.
        if (version < 3) {
          const previa = migrado.normativaSeleccionada;
          migrado = {
            ...migrado,
            normativaSeleccionada:
              previa === "NIIF" ? "NIIF" : NORMATIVA_POR_DEFECTO,
            evidencias: [],
          };
        }
        // v4: las propuestas de la IA contienen texto del documento y dejaron de
        // persistirse; se elimina cualquier copia que hubiera quedado guardada.
        if (version < 4) {
          migrado = { ...migrado, propuestasIA: {} };
        }
        return migrado;
      },
      // Doctrina 10 del PRD: Exclusión estricta de File[] no serializables en localStorage
      partialize: (state) => ({
        companyData: state.companyData,
        normativaSeleccionada: state.normativaSeleccionada,
        isConfigured: state.isConfigured,
        activeView: state.activeView,
        theme: state.theme,
        respuestas: state.respuestas,
        preguntaActualIndex: state.preguntaActualIndex,
        timeboxRestante: state.timeboxRestante,
        proyectoActivo: state.proyectoActivo,
        cambiosSinGuardar: state.cambiosSinGuardar,
        evidencias: state.evidencias,
        correlativoEvidencias: state.correlativoEvidencias,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);

// Hook auxiliar para control de hidratación en componentes SSR
export function useHasHydrated() {
  const [hasHydrated, setHasHydrated] = useState(false);
  useEffect(() => {
    setHasHydrated(true);
  }, []);
  return hasHydrated;
}



