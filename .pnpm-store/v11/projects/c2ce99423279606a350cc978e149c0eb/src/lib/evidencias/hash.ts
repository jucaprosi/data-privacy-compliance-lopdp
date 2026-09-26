/**
 * Huella criptográfica de evidencias documentales.
 *
 * El archivo se lee y se resume en el navegador: su contenido nunca sale del
 * equipo del usuario. Solo la huella SHA-256 y los metadatos se registran.
 */

export const TAMANO_MAXIMO_EVIDENCIA_BYTES = 50 * 1024 * 1024;

export class EvidenciaDemasiadoGrandeError extends Error {
  readonly tamanoBytes: number;

  constructor(nombreArchivo: string, tamanoBytes: number) {
    super(
      `"${nombreArchivo}" pesa ${formatearTamano(tamanoBytes)} y supera el máximo de ${formatearTamano(
        TAMANO_MAXIMO_EVIDENCIA_BYTES
      )} admitido para calcular su huella en el navegador.`
    );
    this.name = "EvidenciaDemasiadoGrandeError";
    this.tamanoBytes = tamanoBytes;
  }
}

function bufferAHex(buffer: ArrayBuffer): string {
  return Array.from(new Uint8Array(buffer), (byte) =>
    byte.toString(16).padStart(2, "0")
  ).join("");
}

/** Calcula la huella SHA-256 del contenido del archivo, en hexadecimal minúsculo. */
export async function calcularSha256(file: File): Promise<string> {
  if (file.size > TAMANO_MAXIMO_EVIDENCIA_BYTES) {
    throw new EvidenciaDemasiadoGrandeError(file.name, file.size);
  }
  if (typeof crypto === "undefined" || !crypto.subtle) {
    throw new Error(
      "Este navegador no expone la API criptográfica necesaria (se requiere un contexto seguro: HTTPS o localhost)."
    );
  }
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return bufferAHex(digest);
}

export function formatearTamano(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Hash abreviado para listados: primeros y últimos caracteres. */
export function abreviarHash(hash: string, extremos = 8): string {
  if (hash.length <= extremos * 2 + 1) return hash;
  return `${hash.slice(0, extremos)}…${hash.slice(-extremos)}`;
}

export function formatearFechaRegistro(iso: string): string {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return iso;
  return fecha.toLocaleString("es-EC", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
