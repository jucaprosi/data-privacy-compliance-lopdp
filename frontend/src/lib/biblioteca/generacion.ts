// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Cliente de la generación de Word y Excel (BIB-205). El servidor decide tenant, permisos, faltantes y
 * contenido; aquí solo se pide, se lista y se descarga.
 */
import { fetchAutenticado } from "@/lib/auth";
import { cabecerasDeMiembro } from "@/lib/auth/cabeceras";
import { mensajeDelServidor, ROLES_EDITORES } from "@/lib/biblioteca/http";

export type ModoGeneracion = "borrador" | "revision";
export type FormatoGeneracion = "docx" | "xlsx";

export interface Generacion {
  id: string;
  borrador_id: string;
  modo: ModoGeneracion;
  formato: FormatoGeneracion;
  estado: "borrador" | "para_revision";
  plantilla_sha256: string;
  instantanea_sha256: string;
  archivo_sha256: string;
  nombre_archivo: string;
  bytes: number;
  faltantes: string[];
  creado_en: string;
}

const RUTA = "/api/v1/biblioteca/generaciones";
const enc = encodeURIComponent;

async function leer<T>(respuesta: Response, porDefecto: string): Promise<T> {
  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) throw new Error(mensajeDelServidor(datos, porDefecto));
  return datos as T;
}

export async function listarGeneraciones(borradorId: string): Promise<Generacion[]> {
  return leer(await fetchAutenticado(`${RUTA}/borradores/${enc(borradorId)}`, { cache: "no-store" },
    cabecerasDeMiembro(ROLES_EDITORES)), "No se pudieron cargar los archivos generados.");
}

export async function generar(borradorId: string, modo: ModoGeneracion, formato: FormatoGeneracion): Promise<Generacion> {
  return leer(await fetchAutenticado(`${RUTA}/borradores/${enc(borradorId)}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ modo, formato }),
  }, cabecerasDeMiembro(ROLES_EDITORES)), "No se pudo generar el archivo.");
}

export async function descargarGeneracion(generacion: Generacion): Promise<void> {
  const respuesta = await fetchAutenticado(`${RUTA}/${enc(generacion.id)}/archivo`, { cache: "no-store" },
    cabecerasDeMiembro(ROLES_EDITORES));
  if (!respuesta.ok) throw new Error("No se pudo descargar el archivo.");
  const url = URL.createObjectURL(await respuesta.blob());
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = generacion.nombre_archivo;
  enlace.click();
  URL.revokeObjectURL(url);
}
