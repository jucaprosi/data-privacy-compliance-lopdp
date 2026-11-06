// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/** Reutilización y procedencia (BIB-202): origen de cada dato, instantánea emitida y aviso de cambios. */
import { httpBiblioteca } from "./http";

export type TipoFuente = "organizacion" | "dpd" | "rat" | "diagnostico";
export interface OrigenCampo {
  clave: string; valor: string; fuente: TipoFuente; fuente_id: string; revision: string | null;
  fecha: string | null; validador: string | null; estado: "validado" | "sin_validar";
  limitacion: string | null; huella: string;
}
export interface Instantanea {
  documento_id: string | null; revision_documento: number | null; campos: OrigenCampo[];
  sha256: string; tomada_en: string | null;
}
export interface CambioFuente { clave: string; emitido: string | null; actual: string | null }
export interface AvisoCambios {
  documento_id: string; cambiado: boolean; cambios: CambioFuente[]; emitida: Instantanea; actual: Instantanea;
}
export interface PropuestaCorreccion {
  documento_id: string; clave: string; valor_canonico: string; valor_propuesto: string; motivo: string;
  estado: "propuesto"; fuente: TipoFuente; fuente_id: string;
}

const base = "/biblioteca/fuentes";
const doc = (id: string) => `${base}/documentos/${encodeURIComponent(id)}`;
export const procedenciaActual = () => httpBiblioteca<Instantanea>(`${base}/procedencia`);
export const emitirInstantanea = (documentoId: string) =>
  httpBiblioteca<Instantanea>(`${doc(documentoId)}/instantanea`, { method: "POST" });
export const cambiosDeFuente = (documentoId: string) => httpBiblioteca<AvisoCambios>(`${doc(documentoId)}/cambios`);
export const proponerCorreccion = (documentoId: string, clave: string, valorPropuesto: string, motivo: string) =>
  httpBiblioteca<PropuestaCorreccion>(`${doc(documentoId)}/propuestas`, {
    method: "POST", body: JSON.stringify({ clave, valor_propuesto: valorPropuesto, motivo }),
  });
