// ¤adpa ¤rbac-tenant
/** BIB-208: cliente de los mapas de captura/salida de las ocho fichas iniciales. */
import { httpBiblioteca } from "@/lib/biblioteca/http";

export interface CampoFicha {
  clave: string; etiqueta: string; tipo: string; requisito: "O" | "C" | "D"; valores: string[];
  editable: boolean; columna: string | null; seccion: string | null;
}
export interface MapaFicha {
  codigo: string; modo: "tabla" | "secciones"; version_esquema: string; plantilla: string; interfaz: string;
  secciones: string[]; colecciones: string[]; estado_generacion: string; campos: CampoFicha[];
}

export const listarFichasIniciales = () => httpBiblioteca<MapaFicha[]>("/biblioteca/fichas-iniciales");
