/**
 * Flujo de subida de evidencia: URL prefirmada, subida del archivo y registro con su huella.
 *
 * Se orquesta aquí, y no con el store, porque el registro solo debe ocurrir si el archivo llegó:
 * si la subida falla (respuesta no satisfactoria o error de red), se corta el flujo y no queda
 * registrada una evidencia de un archivo que no existe.
 */
import { roadmapApi } from "@/lib/roadmap/cliente";
import { calcularSha256 } from "@/lib/evidencias/hash";
import { ApiError } from "@/types/roadmap";
import type { TaskEvidence } from "@/types/roadmap";

export type PasoSubida = "preparando" | "solicitando" | "subiendo" | "registrando";

export const MENSAJE_PASO: Readonly<Record<PasoSubida, string>> = {
  preparando: "Calculando la huella del archivo…",
  solicitando: "Solicitando la autorización de subida…",
  subiendo: "Subiendo el archivo…",
  registrando: "Registrando la evidencia…",
};

export async function subirEvidencia(
  tareaId: string,
  archivo: File,
  alPaso?: (paso: PasoSubida) => void,
): Promise<TaskEvidence> {
  const tipo = archivo.type || "application/octet-stream";

  alPaso?.("preparando");
  const huella = await calcularSha256(archivo);

  alPaso?.("solicitando");
  const autorizacion = await roadmapApi.getEvidenceUploadUrl(tareaId, {
    filename: archivo.name,
    mime_type: tipo,
    file_size: archivo.size,
  });

  alPaso?.("subiendo");
  let respuesta: Response;
  try {
    respuesta = await fetch(autorizacion.upload_url, {
      method: "PUT",
      headers: { "Content-Type": tipo },
      body: archivo,
    });
  } catch {
    throw new ApiError(0, "No se pudo subir el archivo: falló la conexión con el almacenamiento.", "UPLOAD_FAILED", "retry_upload");
  }
  if (!respuesta.ok) {
    throw new ApiError(
      respuesta.status,
      `El almacenamiento rechazó el archivo (HTTP ${respuesta.status}).`,
      "UPLOAD_FAILED",
      "retry_upload",
    );
  }

  alPaso?.("registrando");
  return roadmapApi.registerEvidence(tareaId, {
    r2_key: autorizacion.r2_key,
    mime_type: tipo,
    file_size: archivo.size,
    file_hash: huella,
  });
}
