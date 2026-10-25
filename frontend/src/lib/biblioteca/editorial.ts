// ¤adpa
// ¤¤developer-architect
import { httpBiblioteca } from "./http";

export type Capacidad = "editor" | "revisor_tecnico" | "revisor_juridico" | "publicador";
export interface Ficha {
  nombre: string; objetivo: string; fuentes: string; fecha_revision: string;
  instrucciones: string; dependencias: string; restricciones: string;
}
export interface Version {
  id: string; codigo: string; version: string; formato: "DOCX" | "XLSX";
  ficha: Ficha | null; responsable_id: string; autores: string[];
  estado: "en_revision" | "publicada" | "retirada" | "sustituida";
  generacion: number; sha256: string | null; nombre_archivo: string | null;
  sustituye_id: string | null; creada_en: string;
}
export interface Revision {
  version_id: string; generacion: number; tipo: "tecnica" | "juridica";
  aprobado: boolean; revisor_id: string; comentario: string; creada_en: string;
}
export interface CatalogoEditorial {
  actor_id: string; capacidades: Capacidad[]; versiones: Version[]; revisiones: Revision[];
}
export interface EventoEditorial {
  actor_id: string; alcance: string; accion: string; generacion: number; motivo: string | null; creada_en: string;
}
const base = "/editorial";
export const listarEditorial = () => httpBiblioteca<CatalogoEditorial>(base);
export const crearVersion = (codigo: string, version: string, formato: string, sustituye_id: string | null) =>
  httpBiblioteca<Version>(`${base}/versiones`, { method: "POST", body: JSON.stringify({ codigo, version, formato, sustituye_id }) });
export const guardarFicha = (v: Version, ficha: Ficha) => httpBiblioteca<Version>(`${base}/versiones/${v.id}/ficha`, {
  method: "PUT", body: JSON.stringify({ ficha, generacion: v.generacion }),
});
export const dictaminar = (v: Version, tipo: string, aprobado: boolean, comentario: string) =>
  httpBiblioteca<Version>(`${base}/versiones/${v.id}/revisiones`, {
    method: "POST", body: JSON.stringify({ tipo, aprobado, comentario, generacion: v.generacion }),
  });
export const cambiarEstado = (v: Version, accion: "publicar" | "retirar", motivo: string) =>
  httpBiblioteca<Version>(`${base}/versiones/${v.id}/${accion}`, {
    method: "POST", body: JSON.stringify({ motivo, generacion: v.generacion }),
  });
export const leerHistorial = (v: Version) => httpBiblioteca<EventoEditorial[]>(`${base}/versiones/${v.id}/historial`);
export async function cargarArchivo(v: Version, archivo: File): Promise<Version> {
  if (!archivo.size || archivo.size > 10 * 1024 * 1024) throw new Error("El archivo debe contener datos y no superar 10 MB.");
  const contenido = await new Promise<string>((resolve, reject) => {
    const lector = new FileReader();
    lector.onload = () => resolve(String(lector.result).split(",")[1]);
    lector.onerror = () => reject(new Error("No se pudo leer el archivo."));
    lector.readAsDataURL(archivo);
  });
  return httpBiblioteca<Version>(`${base}/versiones/${v.id}/archivo`, {
    method: "PUT", body: JSON.stringify({ nombre: archivo.name, contenido_base64: contenido, generacion: v.generacion }),
  });
}
