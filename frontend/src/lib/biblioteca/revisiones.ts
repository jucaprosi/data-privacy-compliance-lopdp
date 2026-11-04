// ¤adpa ¤rbac-tenant
import { cabecerasDeTenant, fetchAutenticado } from "@/lib/auth";

export type TipoParticipacion = "revision" | "asesoria" | "supervision";
export interface RevisionDocumental {
  id: string; documento_id: string; revision: number; sha256: string; revisor_id: string;
  tipo_participacion: TipoParticipacion; estado: "asignada" | "devuelta" | "aprobada";
  observaciones: string | null; criterio_aprobacion: string | null;
}

const RUTA = "/api/v1/biblioteca/revisiones";

async function mutar(ruta: string, cuerpo: object): Promise<RevisionDocumental> {
  const respuesta = await fetchAutenticado(ruta, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo),
  }, cabecerasDeTenant());
  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) throw new Error(typeof datos?.detail === "string" ? datos.detail : "No se pudo completar la revisión.");
  return datos as RevisionDocumental;
}

export const enviarRevision = (documentoId: string, revisorId: string, tipo: TipoParticipacion) =>
  mutar(`${RUTA}/documentos/${encodeURIComponent(documentoId)}`, { revisor_id: revisorId, tipo_participacion: tipo });
export const devolverRevision = (revisionId: string, motivo: string) =>
  mutar(`${RUTA}/${encodeURIComponent(revisionId)}/devolver`, { motivo });
export const aprobarRevision = (revisionId: string, criterio: string) =>
  mutar(`${RUTA}/${encodeURIComponent(revisionId)}/aprobar`, { criterio });

