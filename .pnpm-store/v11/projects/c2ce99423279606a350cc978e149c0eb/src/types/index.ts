/**
 * Tipos de datos e interfaces para JUBYS Plataforma LOPDP 360.
 * Abarca las 7 salas ADPA, scoring multidimensional, contexto multi-tenant y copiloto.
 */

import type { NormativaId } from "@/lib/normativas";

export type ModuloADPA =
  | "configuracion"
  | "diagnostico"
  | "rat"
  | "riesgos_mtge"
  | "dpo_cockpit"
  | "auditoria_capa"
  | "evidencias"
  | "regulacion_rag"
  | "incidentes"
  | "reportes";

export interface FichaOrganizacion {
  sector: string;
  tamano: string;
  emplea_nube: boolean;
  trata_datos_salud: boolean;
  emplea_ia: boolean;
  videovigilancia: boolean;
  transferencias_internacionales: boolean;
}

export interface PreguntaDiagnostico {
  id_pregunta: string;
  dominio_id: string;
  enunciado: string;
  referencia_normativa: string;
  es_nucleo: boolean;
  evidencia_esperada: string;
}

export type NivelEvidencia = "E0_SIN_EVIDENCIA" | "E1_DOCUMENTADA" | "E2_IMPLEMENTADA" | "E3_PROBADA";

export interface RespuestaDiagnosticoItem {
  id_pregunta: string;
  respuesta_afirmativa: boolean;
  nivel_evidencia: NivelEvidencia;
  rationale?: string;
}

export interface ScoringDiagnostico {
  madurez_spdp: number;
  madurez_nivel_etiqueta: string;
  porcentaje_conformidad_juridica: number;
  cobertura_evidencia_porcentaje: number;
  brechas_criticas_abiertas: number;
  preguntas_respondidas_total: number;
  duracion_minutos_estimada: number;
}

export interface ActividadRAT {
  id?: string;
  codigo: string;
  nombre: string;
  area_responsable: string;
  finalidad: string;
  base_legal: string;
  categorias_titulares: string[];
  datos_sensibles: boolean;
  volumen_titulares_estimado: number;
  transferencia_internacional: boolean;
  requiere_eipd: boolean;
  es_gran_escala: boolean;
}

export interface ResultadoMTGE {
  actividad_rat_id: string;
  puntaje_mtge: number;
  es_gran_escala: boolean;
  detona_dpo_obligatorio: boolean;
  detona_eipd_obligatoria: boolean;
  criterio_activacion: string;
  rationale: string;
}

export interface DictamenDPO {
  id?: string;
  tenant_id?: string;
  dpo_id: string;
  tipo: string;
  asunto: string;
  referencia_normativa: string;
  cuerpo: string;
  fecha_emision?: string;
  acuse_recibo_alta_direccion?: boolean;
}

export interface TicketCAPA {
  id?: string;
  tenant_id?: string;
  control_id: string;
  severidad: string;
  descripcion_hallazgo: string;
  causa_raiz: string;
  accion_correctiva: string;
  responsable_implementacion_id: string;
  auditor_verificador_id?: string;
  estado?: string;
}

export interface EvidenciaRegistro {
  id?: string;
  codigo: string;
  nombre_archivo: string;
  sha256_hash: string;
  storage_path: string;
  calidad: string;
  propietario_id: string;
}

export interface RespuestaRAG {
  pregunta: string;
  respuesta: string;
  citas_normativas: string[];
  confianza: number;
  fuente_oficial_verificada: boolean;
}

// 8. Tipos canónicos para Configuración de Proyecto y Selector de Normativas
export type { NormativaAuditoria, CompanyData } from "@/store/useAuditStore";

// 9. Tipos Canónicos para Snapshots Inmutables de Auditoría (Módulo 3 & Doctrina 10)
export type NivelEvidenciaSimple = "E0" | "E1" | "E2" | "E3";

export interface RespuestaSnapshotItem {
  id_pregunta: string;
  respuesta_afirmativa: boolean;
  nivel_evidencia: NivelEvidenciaSimple | string;
  rationale?: string;
}

export interface ScoringFinalSnapshot {
  madurez: number; // Porcentaje de madurez SPDP (0 - 100%)
  coberturaEvidencias: number; // Cobertura de evidencias probatorias E1-E3 (0 - 100%)
  conformidadLegalBooleana: boolean; // ¿Cumple 100% de los núcleos legales no compensables?
  riesgoResidual: number; // Nivel de riesgo residual (0 - 100%)
  detalles?: {
    brechasCriticas: number;
    preguntasRespondidas: number;
  };
}

export interface AuditSnapshot {
  id: string; // Identificador único (UUID criptográfico o timestamp sellado)
  fechaCierre: string; // Timestamp ISO 8601 sellado por el servidor
  empresa: {
    razonSocial: string;
    sector: string;
    tamano: string;
  };
  /** Identificador del catálogo de normativas; los snapshots históricos pueden conservar etiquetas anteriores. */
  normativa: NormativaId | string;
  versionNormativa: string; // ej: "LOPDP-EC-2026.v1"
  respuestasSnapshot: RespuestaSnapshotItem[];
  scoringFinal: ScoringFinalSnapshot;
  sha256Seal?: string; // Sello de integridad criptográfica
}

export type NuevoSnapshotInput = Omit<AuditSnapshot, "id" | "fechaCierre" | "sha256Seal">;

// 10. Tipos Canónicos para Playbook de Incidentes y SLA (Ley Ciberseguridad 2026)
export * from "./incidente";

// 11. Tipos Canónicos para RAT Maestro y MTGE (Resolución SPDP-SPD-2026-0005-R)
export * from "./rat";

// 12. Tipos Canónicos para Gestión de Derechos ARCO+ (LOPDP Arts. 21-24, 37 | Doctrina 3)
export * from "./arco";

// 13. Tipos Canónicos para Gestión de Hallazgos y CAPA (INV_CAPA_SOD | Doctrina 4 y 10)
export * from "./capa";
