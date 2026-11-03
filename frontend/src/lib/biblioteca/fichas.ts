// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/** Cliente de la ficha de plantilla (BIB-103) y de «Usar en esta organización» (contrato de BIB-107). */
import { httpBiblioteca } from "./http";

export interface FichaEditorial {
  nombre: string; objetivo: string; fuentes: string; fecha_revision: string;
  instrucciones: string; dependencias: string; restricciones: string;
}
export type OrigenVariable = "organizacion" | "delegado" | "persona" | "al_crear" | "al_aprobar";
export interface VariablePlantilla {
  clave: string; etiqueta: string; ambito: string; origen: OrigenVariable;
  obligatoria: boolean; disponible: boolean;
}
export interface AvisoPlantilla { cuando: string; nivel: "info" | "alto"; texto: string }
export interface FichaPlantilla {
  id: string; codigo: string; nombre: string; tipo: string; fuente: "smartcidi" | "organizacion";
  version: string | number; formato: "MD"; ola: number;
  validacion_legal: "pendiente" | "en_revision" | "validada" | "con_observaciones";
  estado_editorial: "publicada" | "mi_plantilla";
  fecha_corte_normativo: string; base_lopdp: string; revision_meses: number;
  ficha: FichaEditorial | null; avisos: AvisoPlantilla[];
  origen_plantilla_id: string | null; origen_version: string | null;
  cuerpo_markdown: string; variables: VariablePlantilla[];
  vista_previa: { demostrativa: true; aviso: string; markdown: string };
  acciones: { usar: boolean; copiar: boolean };
}
export interface CopiaCreada {
  id: string; fuente: "organizacion"; nombre: string; version: number;
  origen_plantilla_id: string; origen_version: string;
}
/** Lo mínimo que esta vista lee del `Documento` de BIB-107 (docs/biblioteca-pmv.md, apartado c). */
export interface DocumentoCreado { id: string; estado: string; variables_faltantes: string[] }

export const obtenerFicha = (id: string) =>
  httpBiblioteca<FichaPlantilla>(`/biblioteca/plantillas/${encodeURIComponent(id)}`);
export const crearCopia = (id: string) =>
  httpBiblioteca<CopiaCreada>(`/biblioteca/plantillas/${encodeURIComponent(id)}/copias`, { method: "POST" });
export const usarEnOrganizacion = (plantilla_id: string) =>
  httpBiblioteca<DocumentoCreado>("/biblioteca/documentos", { method: "POST", body: JSON.stringify({ plantilla_id }) });
