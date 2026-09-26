/**
 * Contrato de la evidencia documental del assessment.
 *
 * La plataforma no conserva el archivo: registra su huella SHA-256, calculada en
 * el navegador, y los controles que respalda. La huella permite demostrar más
 * tarde que un documento presentado es exactamente el que se registró.
 *
 * Regla de evidencia verificada (Doctrina 3): un control cuenta como verificado
 * solo si tiene al menos una evidencia vinculada. El nivel E0-E3 que declara el
 * auditor sin documento vinculado se conserva como "declarado" y no puede
 * sellarse en un snapshot de auditoría.
 */

import type { NormativaId } from "@/lib/normativas";

export interface EvidenciaDocumental {
  id: string;
  /** Código correlativo legible, p. ej. EVD-0007. */
  codigo: string;
  nombreArchivo: string;
  tamanoBytes: number;
  tipoMime: string;
  /** Huella SHA-256 en hexadecimal minúsculo (64 caracteres). */
  sha256: string;
  normativa: NormativaId;
  /** Identificadores de pregunta (1-80) que esta evidencia respalda. */
  controlesVinculados: number[];
  registradaEn: string;
}

export type NuevaEvidencia = Pick<
  EvidenciaDocumental,
  "nombreArchivo" | "tamanoBytes" | "tipoMime" | "sha256"
> & {
  controlesVinculados?: number[];
};

export const PATRON_SHA256 = /^[a-f0-9]{64}$/;

/** Valida una evidencia leída de una fuente no confiable (proyecto guardado). */
export function esEvidenciaValida(valor: unknown): valor is EvidenciaDocumental {
  if (!valor || typeof valor !== "object") return false;
  const v = valor as Record<string, unknown>;
  return (
    typeof v.id === "string" &&
    typeof v.codigo === "string" &&
    typeof v.nombreArchivo === "string" &&
    typeof v.normativa === "string" &&
    typeof v.sha256 === "string" &&
    PATRON_SHA256.test(v.sha256) &&
    Array.isArray(v.controlesVinculados) &&
    v.controlesVinculados.every((c) => Number.isInteger(c))
  );
}

/** Número correlativo de un código EVD-NNNN (0 si no tiene forma válida). */
export function correlativoDeCodigo(codigo: string): number {
  const n = Number.parseInt(codigo.replace(/\D/g, ""), 10);
  return Number.isFinite(n) ? n : 0;
}

export type ModoEvidencia = "declarado" | "verificado";
