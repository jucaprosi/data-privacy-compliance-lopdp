// ¤adpa ¤rbac-tenant
import { fetchAutenticado } from "@/lib/auth";
import { cabecerasDeMiembro } from "@/lib/auth/cabeceras";
import { mensajeDelServidor, ROLES_GESTION_DOCUMENTAL } from "@/lib/biblioteca/http";

export type TipoParticipacion = "revision" | "asesoria" | "supervision";
export interface RevisionDocumental {
  id: string; documento_id: string; revision: number; sha256: string; revisor_id: string;
  tipo_participacion: TipoParticipacion; estado: "asignada" | "devuelta" | "aprobada";
  observaciones: string | null; criterio_aprobacion: string | null;
}

const RUTA = "/api/v1/biblioteca/revisiones";

/** `roles`: los del `require_role` de la ruta; devolver y aprobar admiten a cualquier miembro (el servidor exige al revisor). */
async function mutar(ruta: string, cuerpo: object, roles?: readonly string[]): Promise<RevisionDocumental> {
  const respuesta = await fetchAutenticado(ruta, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo),
  }, cabecerasDeMiembro(roles));
  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) throw new Error(mensajeDelServidor(datos, "No se pudo completar la revisión."));
  return datos as RevisionDocumental;
}

export const enviarRevision = (documentoId: string, revisorId: string, tipo: TipoParticipacion) =>
  mutar(`${RUTA}/documentos/${encodeURIComponent(documentoId)}`, { revisor_id: revisorId, tipo_participacion: tipo },
    ROLES_GESTION_DOCUMENTAL);
export const devolverRevision = (revisionId: string, motivo: string) =>
  mutar(`${RUTA}/${encodeURIComponent(revisionId)}/devolver`, { motivo });
export const aprobarRevision = (revisionId: string, criterio: string) =>
  mutar(`${RUTA}/${encodeURIComponent(revisionId)}/aprobar`, { criterio });

