/**
 * Vigencia, visibilidad y paquete para inspección de las evidencias (EVI-02).
 *
 * Solo existe con la subida firmada encendida en el servidor. Quién define la vigencia y la visibilidad (el DPO)
 * y qué ve cada rol lo decide el servidor; aquí solo se muestra lo que devuelve y se baja el paquete.
 */
import { fetchAutenticado } from "@/lib/auth";
import { cabecerasComo, rolParaLeer } from "@/lib/diagnostico/roles";
import { requestJson } from "@/lib/roadmap/cliente";

export const ROLES_VISIBILIDAD = ["dpo", "coordinador", "implementador", "admin_organizacion"] as const;
export type RolVisibilidad = (typeof ROLES_VISIBILIDAD)[number];

export const ETIQUETA_ROL: Record<RolVisibilidad, string> = {
  dpo: "DPO",
  coordinador: "Coordinador",
  implementador: "Implementador",
  admin_organizacion: "Administrador de la organización",
};

export interface AtributosDocumento {
  documento_id: string;
  codigo: string;
  nombre_archivo: string;
  tipo_mime: string;
  tamano_bytes: number;
  sha256_hash: string;
  subido_en: string;
  vence_en: string | null;
  vigente: boolean;
  visible_para: string[];
  controles_vinculados: number[];
}

/** Fecha ISO (aaaa-mm-dd) como dd/mm/aaaa (es-EC), sin pasar por la zona horaria. */
export function formatearFecha(iso: string | null): string {
  const [anio, mes, dia] = (iso ?? "").split("-");
  return anio && mes && dia ? `${dia}/${mes}/${anio}` : "";
}

/** Mensajes fijos por código: el texto técnico del servidor no se muestra (UX/UI). */
export function mensajeDePaquete(codigo: string | undefined): string {
  switch (codigo) {
    case "EVI_PAQUETE_VACIO":
      return "No hay documentos vigentes y visibles para tu rol que incluir en el paquete.";
    case "EVI_PAQUETE_DEMASIADO_GRANDE":
      return "El paquete es demasiado grande para descargarlo de una vez. Avisa al equipo de EVYDENTIA.";
    case "EVI_PAQUETE_INTEGRIDAD":
      return "Un documento no coincide con su registro de integridad y el paquete no se generó. Avisa al DPO y al equipo de EVYDENTIA.";
    case "EVI_SIN_PERMISO_PARA_ATRIBUTOS":
      return "Solo el DPO puede cambiar la vigencia y la visibilidad de un documento.";
    default:
      return "No se pudo completar la operación. Inténtalo de nuevo.";
  }
}

export async function cargarAtributos(): Promise<AtributosDocumento[]> {
  const rol = await rolParaLeer();
  if (!rol) throw new Error("Tu rol no consulta las evidencias de la organización.");
  return (await requestJson<{ documentos: AtributosDocumento[] }>("/evidencias/atributos", { headers: { "X-Role": rol } }))
    .documentos;
}

export async function definirAtributos(
  documentoId: string,
  venceEn: string | null,
  visiblePara: string[] | null
): Promise<void> {
  await requestJson(`/evidencias/documentos/${encodeURIComponent(documentoId)}/atributos`, {
    method: "PUT",
    headers: { "X-Role": "dpo" },
    body: JSON.stringify({ vence_en: venceEn, visible_para: visiblePara }),
  });
}

/** Baja el ZIP del paquete con la sesión (no con una navegación) y lo guarda en el navegador. */
export async function descargarPaquete(): Promise<void> {
  const rol = await rolParaLeer();
  if (!rol) throw Object.assign(new Error("sin rol"), { code: "EVI_SIN_ROL" });
  const respuesta = await fetchAutenticado("/api/v1/evidencias/paquete-inspeccion", { cache: "no-store" }, cabecerasComo(rol));
  if (!respuesta.ok) {
    const cuerpo = (await respuesta.json().catch(() => null)) as { code?: string } | null;
    throw Object.assign(new Error("paquete"), { code: cuerpo?.code });
  }
  const url = URL.createObjectURL(await respuesta.blob());
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = `paquete-inspeccion-${new Date().toISOString().slice(0, 10)}.zip`;
  enlace.style.display = "none";
  document.body.appendChild(enlace);
  enlace.click();
  document.body.removeChild(enlace);
  URL.revokeObjectURL(url);
}
