/**
 * Etiquetas visibles de los estados de cumplimiento de cada control.
 *
 * Los valores internos ("Conforme", "Parcial", "No Conforme") son identificadores
 * persistidos en el navegador y en los snapshots sellados; no se renombran para
 * no invalidar datos existentes. Lo que ve la persona usuaria sale de aquí.
 */
export const ETIQUETA_ESTADO_CUMPLIMIENTO: Record<string, string> = {
  Conforme: "Implementado",
  Parcial: "Parcial",
  "No Conforme": "No Implementado",
  Pendiente: "Pendiente",
  "Sin sustento": "Sin sustento",
};

export function etiquetaEstadoCumplimiento(estado: string): string {
  return ETIQUETA_ESTADO_CUMPLIMIENTO[estado] ?? estado;
}
