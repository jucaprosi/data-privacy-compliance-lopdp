// ¤adpa ¤rbac-tenant
import { httpBiblioteca } from "./http";

export type ClaveIndicador = "acciones" | "documentos" | "decisiones";
export interface Exclusion { motivo: string; cantidad: number | null }
export interface Indicador {
  clave: ClaveIndicador; titulo: string; fecha_corte: string; categoria_foco: string; valor_foco: number;
  denominador: number; conteos: Record<string, number>; sin_mapear: number; exclusiones: Exclusion[];
  avance_implementacion: number | null; etiqueta_avance: string; origen: string;
}
export interface Indicadores { fecha_corte: string; etiqueta: string; indicadores: Indicador[] }
export interface RegistroOrigen { id: string; categoria: string; estado_origen: string | null; descripcion: string; origen: string }
export interface RegistrosIndicador { clave: ClaveIndicador; categoria: string | null; fecha_corte: string; registros: RegistroOrigen[] }

const base = "/biblioteca/indicadores";
export const obtenerIndicadores = () => httpBiblioteca<Indicadores>(base);
export const registrosDeIndicador = (clave: ClaveIndicador, categoria?: string) =>
  httpBiblioteca<RegistrosIndicador>(
    `${base}/${clave}/registros${categoria ? `?categoria=${encodeURIComponent(categoria)}` : ""}`);

export const NOMBRES_CATEGORIA: Record<string, string> = {
  verificada: "Verificadas", no_conforme: "No conformes", pendiente: "Pendientes de verificación",
  pendiente_revision: "Pendientes de revisión", borrador: "En borrador", aprobado: "Aprobados",
  vencido: "Revisión vencida", sin_informacion: "Sin información", decidida: "Decididas",
  sin_mapear: "Estado sin mapear",
};
