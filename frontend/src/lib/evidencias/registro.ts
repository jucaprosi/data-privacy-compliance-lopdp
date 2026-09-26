/**
 * Registro de un archivo como evidencia documental.
 *
 * Punto único por el que entra un documento al registro, tanto desde la pantalla
 * de Configuración como desde una pregunta del cuestionario: valida el formato
 * contra la normativa, calcula la huella en el navegador, registra la evidencia
 * (vinculándola a los controles indicados) y recuerda el archivo en memoria para
 * poder analizarlo durante la sesión.
 */

import { useAuditStore } from "@/store/useAuditStore";
import { calcularSha256 } from "@/lib/evidencias/hash";
import { extensionPermitida, resolverNormativa } from "@/lib/normativas";
import { recordarArchivo } from "@/lib/preanalisis/archivosSesion";
import type { EvidenciaDocumental } from "@/lib/evidencias/tipos";

export type ResultadoRegistro =
  | { ok: true; evidencia: EvidenciaDocumental; duplicada: boolean }
  | { ok: false; error: string };

export interface OpcionesRegistro {
  /** Controles (ids 1-80) que la evidencia respalda desde el registro. */
  controles?: number[];
}

export async function registrarArchivoComoEvidencia(
  archivo: File,
  opciones: OpcionesRegistro = {}
): Promise<ResultadoRegistro> {
  const normativaInicial = useAuditStore.getState().normativaSeleccionada;
  const normativa = resolverNormativa(normativaInicial);

  if (!extensionPermitida(normativaInicial, archivo.name)) {
    return {
      ok: false,
      error: `Formato no admitido en "${archivo.name}". Para ${normativa.etiquetaCorta} se aceptan: ${normativa.extensiones.join(", ")}.`,
    };
  }

  let sha256: string;
  try {
    sha256 = await calcularSha256(archivo);
  } catch (error) {
    const detalle = error instanceof Error ? error.message : "Error desconocido.";
    return { ok: false, error: `No se pudo calcular la huella de "${archivo.name}". ${detalle}` };
  }

  // El cálculo es asíncrono: si la normativa cambió mientras tanto, la evidencia
  // ya no corresponde al régimen activo y se descarta (Doctrina 10).
  if (useAuditStore.getState().normativaSeleccionada !== normativaInicial) {
    return {
      ok: false,
      error: `La normativa cambió mientras se procesaba "${archivo.name}"; vuelve a cargarlo.`,
    };
  }

  const tienePrevia = new Set(useAuditStore.getState().evidencias.map((e) => e.id));
  const evidencia = useAuditStore.getState().registrarEvidencia({
    nombreArchivo: archivo.name,
    tamanoBytes: archivo.size,
    tipoMime: archivo.type || "application/octet-stream",
    sha256,
    controlesVinculados: opciones.controles,
  });
  recordarArchivo(sha256, archivo);

  return { ok: true, evidencia, duplicada: tienePrevia.has(evidencia.id) };
}
