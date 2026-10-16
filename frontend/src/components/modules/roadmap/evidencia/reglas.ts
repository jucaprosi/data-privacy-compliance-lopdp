/**
 * Reglas del panel de evidencia: qué archivos se aceptan y qué puede hacer cada rol.
 *
 * Los permisos siguen la matriz del PRD (Módulo 5, §5.2) que verifica en el backend
 * tests/test_matriz_permisos.py; la interfaz no concede nada, solo evita ofrecer una acción
 * que el servidor va a rechazar.
 */
import type { OrganizacionRole, TaskEvidence } from "../../../../types/roadmap";

/**
 * Tipos de archivo admitidos como evidencia. Es una restricción de la interfaz para avisar antes
 * de subir: no sustituye la validación del servidor.
 */
export const TIPOS_PERMITIDOS: Readonly<Record<string, readonly string[]>> = {
  "application/pdf": [".pdf"],
  "image/png": [".png"],
  "image/jpeg": [".jpg", ".jpeg"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "text/csv": [".csv"],
  "text/plain": [".txt"],
};

export const EXTENSIONES_PERMITIDAS: readonly string[] = Object.values(TIPOS_PERMITIDOS).flat();

/** Tamaño máximo por archivo en la interfaz: 10 MB. El límite real lo fija el servidor (no verificado aquí). */
export const TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024;

/** Suben evidencia el responsable de área y el encargado (PRD §5.2). */
export function puedeSubir(rol: OrganizacionRole): boolean {
  return rol === "responsable_area" || rol === "encargado";
}

/** Validan o rechazan el encargado, el DPO y el implementador (PRD §5.2). */
export function puedeValidar(rol: OrganizacionRole): boolean {
  return rol === "encargado" || rol === "dpo" || rol === "implementador";
}

/** El responsable de área solo ve la evidencia que subió él; el resto ve toda (PRD §5.2). */
export function evidenciaVisible(rol: OrganizacionRole, usuarioId: string, evidencia: TaskEvidence): boolean {
  if (rol !== "responsable_area") return true;
  return evidencia.uploaded_by === usuarioId;
}

/** Cuatro ojos: quien subió la evidencia no puede validarla. */
export function bloqueaCuatroOjos(usuarioId: string, evidencia: TaskEvidence): boolean {
  return Boolean(evidencia.uploaded_by) && evidencia.uploaded_by === usuarioId;
}

export function nombreDeArchivo(r2Key: string): string {
  const partes = r2Key.split("/");
  return partes[partes.length - 1] || r2Key;
}
