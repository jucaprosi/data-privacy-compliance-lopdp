// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Cliente de descarga controlada de plantillas (BIB-104).
 * Solicita al servidor el enlace temporal firmado y dispara la descarga en el navegador.
 */
import { httpBiblioteca } from "./http";

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

/** Dispara la descarga del archivo en el navegador mediante el enlace temporal. */
export function dispararDescargaEnNavegador(url: string, nombreArchivo: string): void {
  if (typeof document === "undefined") return;
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombreArchivo;
  enlace.style.display = "none";
  document.body.appendChild(enlace);
  enlace.click();
  document.body.removeChild(enlace);
}
