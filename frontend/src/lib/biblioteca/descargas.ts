// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Cliente de descarga controlada de plantillas (BIB-104).
 * Solicita al servidor el enlace temporal firmado y dispara la descarga en el navegador.
 */
import { fetchAutenticado } from "@/lib/auth/fetchAutenticado";
import { ErrorBiblioteca, httpBiblioteca, identidadPara } from "./http";

export interface EnlaceDescarga {
  plantilla_id: string;
  codigo: string;
  version: string;
  formato: string;
  nombre_archivo: string;
  url_descarga: string;
  expira_en_segundos: number;
  aviso_legal: string;
}

/** Solicita un enlace temporal firmado para descargar el archivo maestro editable. */
export async function solicitarDescarga(plantillaId: string): Promise<EnlaceDescarga> {
  return httpBiblioteca<EnlaceDescarga>(
    `/biblioteca/plantillas/${encodeURIComponent(plantillaId)}/descargar`,
    { method: "POST" },
  );
}

/**
 * SEC-19: descarga el archivo con la sesión (`Authorization`), no con una navegación del navegador,
 * y lo guarda con `nombre_archivo`. Si falla lanza `ErrorBiblioteca` con el código del servidor y sin
 * su texto: el botón decide el mensaje por el código. Un 401 ya lo atiende `fetchAutenticado`.
 */
export async function descargarArchivo(enlace: EnlaceDescarga): Promise<void> {
  const ruta = enlace.url_descarga.replace(/^\/api\/v1/, "");
  const respuesta = await fetchAutenticado(enlace.url_descarga, { cache: "no-store" }, identidadPara(ruta));
  if (!respuesta.ok) {
    const cuerpo = (await respuesta.json().catch(() => null)) as { code?: string } | null;
    throw new ErrorBiblioteca(cuerpo?.code ?? "BIB_ERROR_HTTP", "", respuesta.status);
  }
  guardarEnElNavegador(await respuesta.blob(), enlace.nombre_archivo);
}

/** Guarda un archivo ya descargado mediante un enlace temporal en memoria. */
function guardarEnElNavegador(contenido: Blob, nombreArchivo: string): void {
  if (typeof document === "undefined") return;
  const url = URL.createObjectURL(contenido);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombreArchivo;
  enlace.style.display = "none";
  document.body.appendChild(enlace);
  enlace.click();
  document.body.removeChild(enlace);
  URL.revokeObjectURL(url);
}
