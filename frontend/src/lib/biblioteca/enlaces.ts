// ¤adpa ¤rbac-tenant
import { fetchAutenticado } from "@/lib/auth";
import { cabecerasDeMiembro } from "@/lib/auth/cabeceras";
import { mensajeDelServidor, ROLES_GESTION_DOCUMENTAL } from "@/lib/biblioteca/http";

export interface EnlaceDocumento {
  id: string;
  documento_id: string;
  documento_revision: number;
  accion_id: string;
  accion_titulo: string;
  accion_estado: string;
  requisito: string;
  hallazgo_id: string | null;
  hallazgo_titulo: string | null;
  hallazgo_origen: string | null;
  hallazgo_origen_ref: string | null;
  pregunta: string | null;
  assessment_version: number | null;
  creado_por: string;
  creado_en: string;
}

const ruta = (documentoId: string) =>
  `/api/v1/biblioteca/documentos/${encodeURIComponent(documentoId)}/enlaces`;

async function json<T>(respuesta: Response): Promise<T> {
  const cuerpo = await respuesta.json().catch(() => null);
  if (!respuesta.ok) throw new Error(mensajeDelServidor(cuerpo, "No se pudo actualizar los enlaces documentales."));
  return cuerpo as T;
}

export async function listarEnlaces(documentoId: string): Promise<EnlaceDocumento[]> {
  return json(await fetchAutenticado(ruta(documentoId), { cache: "no-store" }, cabecerasDeMiembro()));
}

export async function crearEnlace(
  documentoId: string, accionId: string, revision: number
): Promise<EnlaceDocumento> {
  return json(await fetchAutenticado(ruta(documentoId), {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ accion_id: accionId, revision }),
  }, cabecerasDeMiembro(ROLES_GESTION_DOCUMENTAL)));
}

export async function eliminarEnlace(documentoId: string, enlaceId: string): Promise<void> {
  const respuesta = await fetchAutenticado(`${ruta(documentoId)}/${encodeURIComponent(enlaceId)}`,
    { method: "DELETE" }, cabecerasDeMiembro(ROLES_GESTION_DOCUMENTAL));
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => null);
    throw new Error(mensajeDelServidor(cuerpo, "No se pudo retirar el enlace documental."));
  }
}
