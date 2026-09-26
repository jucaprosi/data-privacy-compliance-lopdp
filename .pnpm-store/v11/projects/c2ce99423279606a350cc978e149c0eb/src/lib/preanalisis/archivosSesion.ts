/**
 * Archivos presentados durante la sesión, por huella SHA-256.
 *
 * Solo viven en memoria: no se persisten ni se transmiten por sí mismos. Permiten
 * analizar un documento ya registrado sin volver a pedirlo. Tras recargar la
 * página se pierden, y el auditor debe volver a presentar el archivo (el sistema
 * comprueba que su huella coincide con la registrada).
 */

const archivos = new Map<string, File>();

export function recordarArchivo(sha256: string, archivo: File): void {
  archivos.set(sha256.toLowerCase(), archivo);
}

export function obtenerArchivo(sha256: string): File | undefined {
  return archivos.get(sha256.toLowerCase());
}

export function olvidarArchivo(sha256: string): void {
  archivos.delete(sha256.toLowerCase());
}

export function limpiarArchivosSesion(): void {
  archivos.clear();
}
