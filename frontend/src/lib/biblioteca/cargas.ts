// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Documentos externos del cliente (BIB-106): contrato de `api/routers/biblioteca_cargas.py`.
 * Reserva → archivo (cuerpo binario) → finalizar como borrador. Solo un archivo limpio se descarga.
 */
import { fetchAutenticado } from "@/lib/auth";
import { ErrorBiblioteca, httpBiblioteca, identidadPara, mensajeDelServidor } from "@/lib/biblioteca/http";

export type EstadoAnalisis = "sin_archivo" | "pendiente" | "limpio" | "infectado" | "error" | "rechazado";
export type FormatoExterno = "DOCX" | "XLSX";
export const TAMANO_MAXIMO = 10 * 1024 * 1024;

export interface Carga {
  id: string; titulo: string; codigo: string; version_propia: string;
  version_maestra: { id: string; codigo: string; version: string } | null;
  formato: FormatoExterno; nombre_archivo: string; tamano_bytes: number | null; sha256: string | null;
  estado_analisis: EstadoAnalisis; descargable: boolean; documento_id: string | null;
  revision_externa: number | null; finalizada: boolean; creado_en: string; expira_en: string;
}

export interface DatosCarga {
  titulo: string; codigo: string; version_propia: string; version_maestra_id?: string; documento_id?: string;
}

export const ESTADOS_ANALISIS: Record<EstadoAnalisis, string> = {
  sin_archivo: "Sin archivo", pendiente: "Análisis pendiente", limpio: "Análisis superado",
  infectado: "Retenido: amenaza detectada", error: "Retenido: el análisis falló", rechazado: "Rechazado",
};

export function formatoDe(nombre: string): FormatoExterno | null {
  const n = nombre.toLowerCase();
  return n.endsWith(".docx") ? "DOCX" : n.endsWith(".xlsx") ? "XLSX" : null;
}

const BASE = "/biblioteca/cargas";

async function binario(ruta: string, init: RequestInit): Promise<Response> {
  const respuesta = await fetchAutenticado(`/api/v1${ruta}`, { ...init, cache: "no-store" },
    identidadPara(ruta, init.method));
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => null);
    throw new ErrorBiblioteca(cuerpo?.code ?? "BIB_ERROR_HTTP",
      mensajeDelServidor(cuerpo, "No se pudo completar la operación."), respuesta.status);
  }
  return respuesta;
}

/** Reserva, envía el archivo y, si el análisis lo deja limpio, lo finaliza como borrador. */
export async function cargarExterno(datos: DatosCarga, archivo: File): Promise<Carga> {
  const formato = formatoDe(archivo.name);
  if (!formato) throw new ErrorBiblioteca("BIB_CARGA_FORMATO_INVALIDO", "Solo se admiten archivos DOCX o XLSX.", 422);
  const reserva = await httpBiblioteca<Carga>(BASE, {
    method: "POST",
    body: JSON.stringify({ ...datos, formato, nombre_archivo: archivo.name, tamano_bytes: archivo.size }),
  });
  const ruta = `${BASE}/${encodeURIComponent(reserva.id)}/archivo`;
  const respuesta = await binario(ruta, {
    method: "PUT", body: await archivo.arrayBuffer(), headers: { "Content-Type": "application/octet-stream" },
  });
  const carga = (await respuesta.json()) as Carga;
  if (carga.estado_analisis !== "limpio") return carga;
  await httpBiblioteca(`${BASE}/${encodeURIComponent(carga.id)}/finalizar`, { method: "POST" });
  return httpBiblioteca<Carga>(`${BASE}/${encodeURIComponent(carga.id)}`);
}

export const listarRevisiones = (documentoId: string) =>
  httpBiblioteca<Carga[]>(`${BASE}?documento_id=${encodeURIComponent(documentoId)}`);

export async function descargarCarga(carga: Carga): Promise<Blob> {
  const respuesta = await binario(`${BASE}/${encodeURIComponent(carga.id)}/archivo`, { method: "GET" });
  return respuesta.blob();
}
