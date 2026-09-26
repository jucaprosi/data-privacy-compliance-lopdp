/**
 * Catálogo canónico de normativas de la plataforma.
 *
 * Es el único punto que decide, para cada normativa, qué banco de preguntas se
 * formula y qué tipos de documento se aceptan como evidencia. Ningún componente
 * debe comparar la normativa contra literales ("PI", "NIIF"...) para tomar esas
 * decisiones: se consulta este módulo.
 */

import type { NormativaAuditoria } from "@/store/useAuditStore";

export type NormativaId = "LOPDP" | "PI" | "NIIF" | "ISO";

export interface NormativaDescriptor {
  id: NormativaId;
  nombre: string;
  etiquetaCorta: string;
  subtitulo: string;
  extensiones: readonly string[];
  /** Valor para el atributo accept del selector de archivos. */
  accept: string;
  descripcionArchivos: string;
  /**
   * Toda normativa puede seleccionarse; este indicador solo dice si ya cuenta
   * con banco de preguntas propio para evaluarse y sellar snapshots.
   */
  bancoDisponible: boolean;
}

export const NORMATIVAS: Readonly<Record<NormativaId, NormativaDescriptor>> = {
  LOPDP: {
    id: "LOPDP",
    nombre: "LOPDP · Protección de Datos Personales",
    etiquetaCorta: "LOPDP",
    subtitulo:
      "Assessment de madurez del SGPDP bajo la Ley Orgánica de Protección de Datos Personales, su Reglamento y la normativa de la SPDP.",
    extensiones: [".pdf", ".docx", ".xlsx", ".csv", ".txt", ".png", ".jpg", ".jpeg"],
    accept: ".pdf,.docx,.xlsx,.csv,.txt,.png,.jpg,.jpeg",
    descripcionArchivos:
      "Políticas, avisos de privacidad, RAT e inventarios, contratos de encargado, EIPD, registros y capturas (.pdf, .docx, .xlsx, .csv, .txt, .png, .jpg)",
    bancoDisponible: true,
  },
  PI: {
    id: "PI",
    nombre: "Propiedad Intelectual & Software",
    etiquetaCorta: "PI",
    subtitulo:
      "Auditoría de derechos de autor, licencias de código (MIT/GPL), marcas registradas y acuerdos de confidencialidad.",
    extensiones: [".pdf", ".docx", ".md", ".txt"],
    accept: ".pdf,.docx,.md,.txt",
    descripcionArchivos:
      "Contratos, NDAs, políticas y licencias de código (.pdf, .docx, .md, .txt)",
    bancoDisponible: false,
  },
  NIIF: {
    id: "NIIF",
    nombre: "NIIF 18 · Normas Financieras",
    etiquetaCorta: "NIIF",
    subtitulo:
      "Auditoría de jerarquías de estados financieros, subtotales obligatorios y conciliaciones MPM.",
    extensiones: [".csv", ".xlsx", ".xbrl", ".ixbrl", ".json", ".xml", ".sql"],
    accept: ".csv,.xlsx,.xbrl,.ixbrl,.json,.xml,.sql",
    descripcionArchivos:
      "Estados financieros y logs de ERP (.csv, .xlsx, .xbrl, .ixbrl, .json, .xml, .sql)",
    bancoDisponible: true,
  },
  ISO: {
    id: "ISO",
    nombre: "ISO 27001 · Seguridad de la Información",
    etiquetaCorta: "ISO",
    subtitulo:
      "Gestión de riesgos de ciberseguridad, controles técnicos y matrices de seguridad de la información.",
    extensiones: [".csv", ".xlsx", ".json", ".xml", ".pdf"],
    accept: ".csv,.xlsx,.json,.xml,.pdf",
    descripcionArchivos: "Matrices y registros de seguridad (.csv, .xlsx, .json, .xml, .pdf)",
    bancoDisponible: false,
  },
};

export const ORDEN_NORMATIVAS: readonly NormativaId[] = ["LOPDP", "NIIF", "PI", "ISO"];

export const NORMATIVA_POR_DEFECTO: NormativaId = "LOPDP";

/** Descriptor de la normativa activa; sin selección rige la normativa por defecto. */
export function resolverNormativa(normativa: NormativaAuditoria): NormativaDescriptor {
  return NORMATIVAS[normativa ?? NORMATIVA_POR_DEFECTO];
}

/** Indica si la normativa se evalúa con el banco de 80 controles del SGPDP. */
export function usaBancoSGPDP(normativa: NormativaAuditoria): boolean {
  return (normativa ?? NORMATIVA_POR_DEFECTO) === "LOPDP";
}

/** Indica si la normativa sigue el flujo contable NIIF 18. */
export function esNormativaFinanciera(normativa: NormativaAuditoria): boolean {
  return normativa === "NIIF";
}

/** Valida la extensión de un archivo contra la lista blanca de la normativa. */
export function extensionPermitida(normativa: NormativaAuditoria, nombreArchivo: string): boolean {
  const ext = "." + (nombreArchivo.split(".").pop() ?? "").toLowerCase();
  return resolverNormativa(normativa).extensiones.includes(ext);
}
