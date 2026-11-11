/**
 * Cliente de los documentos de evidencia guardados y comprobados por el servidor (EVI-01b).
 *
 * El flujo de subida tiene tres pasos: (1) pedir la subida, (2) subir el archivo a la URL firmada del
 * almacén, (3) confirmar: el servidor descarga el archivo, calcula su huella y la compara con la que
 * calculó el navegador. Un documento solo existe si el servidor lo registró; nunca se deja como
 * guardado uno que no pasó por los tres pasos.
 *
 * Las rutas nuevas existen solo con la bandera del servidor encendida: sin ella el estado dice
 * `subida_firmada: false` (o la ruta no existe) y la pantalla conserva el registro anterior.
 * Quién sube y vincula lo decide el servidor; aquí solo se elige con qué rol actuar y qué mostrar.
 */
import { requestJson } from "@/lib/roadmap/cliente";
import { rolParaLeer, rolesDelUsuario } from "@/lib/diagnostico/roles";
import type { EvidenciaDocumental } from "@/lib/evidencias/tipos";
import type { NormativaId } from "@/lib/normativas";

const ROL_DPO = "dpo";
const ROLES_QUE_SUBEN_TRAS_EL_REAL = ["responsable_area", "coordinador"] as const;
const ROLES_CONSULTA = ["dpo", "coordinador", "implementador", "admin_organizacion"] as const;

export interface DocumentoServidor {
  id: string;
  codigo: string;
  nombre_archivo: string;
  tipo_mime: string;
  tamano_bytes: number;
  sha256_hash: string;
  normativa: string;
  subido_por: string;
  subido_en: string;
  retencion_dias: number;
  controles_vinculados: number[];
}

interface FirmaSubida {
  clave: string;
  url: string;
  metodo: string;
  cabeceras: Record<string, string>;
  caduca_en_segundos: number;
}

export interface PermisosEvidencia {
  /** La subida firmada está encendida en el servidor. */
  subidaFirmada: boolean;
  /** El diagnóstico real ya está sellado. */
  real: boolean;
  /** Rol con el que esta persona sube, o null si no puede subir en esta etapa. */
  rolQueSube: string | null;
  puedeVincular: boolean;
  puedeConsultar: boolean;
}

export const SIN_PERMISOS: PermisosEvidencia = {
  subidaFirmada: false,
  real: false,
  rolQueSube: null,
  puedeVincular: false,
  puedeConsultar: false,
};

export function aEvidencia(doc: DocumentoServidor): EvidenciaDocumental {
  return {
    id: doc.id,
    codigo: doc.codigo,
    nombreArchivo: doc.nombre_archivo,
    tamanoBytes: doc.tamano_bytes,
    tipoMime: doc.tipo_mime,
    sha256: doc.sha256_hash,
    normativa: doc.normativa as NormativaId,
    controlesVinculados: [...doc.controles_vinculados],
    registradaEn: doc.subido_en,
    enServidor: true,
  };
}

/** Mensajes fijos por código: el texto técnico del servidor no se muestra a la persona (revisión UX/UI). */
export function mensajeDeSubida(codigo: string | undefined, extensiones: readonly string[]): string {
  switch (codigo) {
    case "EVI_ALMACEN_NO_DISPONIBLE":
      return "El almacén de documentos no está disponible en este momento. El documento no se registró. Inténtalo de nuevo en unos minutos.";
    case "EVIDENCE_TYPE_NOT_ALLOWED":
      return `Este tipo de archivo no se admite. Elige uno de los tipos permitidos: ${extensiones.join(", ")}.`;
    case "EVI_HUELLA_NO_COINCIDE":
      return "El archivo cambió durante la subida y no se registró. Vuelve a subirlo.";
    default:
      return "No se pudo subir el documento. Inténtalo de nuevo.";
  }
}

export async function subidaFirmadaActiva(): Promise<boolean> {
  try {
    return (await requestJson<{ subida_firmada: boolean }>(`/evidencias/estado`)).subida_firmada === true;
  } catch {
    return false;
  }
}

async function diagnosticoRealSellado(): Promise<boolean> {
  const rol = await rolParaLeer();
  if (!rol) return false;
  try {
    const { etapa } = await requestJson<{ etapa: string | null }>("/diagnostico/etapa", {
      headers: { "X-Role": rol },
    });
    return etapa === "real";
  } catch {
    return false;
  }
}

/** Quién puede qué, según el rol y la etapa del diagnóstico (el servidor lo vuelve a comprobar). */
export function permisosPara(roles: readonly string[], real: boolean): Omit<PermisosEvidencia, "subidaFirmada" | "real"> {
  const rolQueSube = real
    ? (ROLES_QUE_SUBEN_TRAS_EL_REAL.find((r) => roles.includes(r)) ?? null)
    : roles.includes(ROL_DPO)
      ? ROL_DPO
      : null;
  return {
    rolQueSube,
    puedeVincular: !real && roles.includes(ROL_DPO),
    puedeConsultar: ROLES_CONSULTA.some((r) => roles.includes(r)),
  };
}

export async function cargarPermisos(): Promise<PermisosEvidencia> {
  if (!(await subidaFirmadaActiva())) return SIN_PERMISOS;
  const [roles, real] = await Promise.all([rolesDelUsuario(), diagnosticoRealSellado()]);
  return { subidaFirmada: true, real, ...permisosPara(roles, real) };
}

export async function cargarDocumentos(): Promise<EvidenciaDocumental[]> {
  const rol = await rolParaLeer();
  if (!rol) throw new Error("Tu rol no consulta las evidencias de la organización.");
  const { documentos } = await requestJson<{ documentos: DocumentoServidor[] }>(`/evidencias/documentos`, {
    headers: { "X-Role": rol },
  });
  return documentos.map(aEvidencia);
}

export type ResultadoSubida =
  | { ok: true; evidencia: EvidenciaDocumental; duplicada: boolean }
  | { ok: false; error: string };

/** Los tres pasos. Cualquier error se devuelve tal cual lo dice el servidor o el almacén. */
export async function subirDocumento(
  archivo: File,
  sha256: string,
  rol: string,
  normativa: string,
  extensiones: readonly string[] = []
): Promise<ResultadoSubida> {
  const tipo = archivo.type || "application/octet-stream";
  try {
    const firma = await requestJson<FirmaSubida>(`/evidencias/subidas`, {
      method: "POST",
      headers: { "X-Role": rol },
      body: JSON.stringify({ nombre_archivo: archivo.name, tipo_mime: tipo, tamano_bytes: archivo.size }),
    });
    const subida = await fetch(firma.url, { method: firma.metodo, headers: firma.cabeceras, body: archivo });
    if (!subida.ok) {
      return { ok: false, error: mensajeDeSubida("EVI_ALMACEN_NO_DISPONIBLE", extensiones) };
    }
    const confirmada = await requestJson<{ duplicada: boolean; documento: DocumentoServidor }>(
      `/evidencias/subidas/confirmar`,
      {
        method: "POST",
        headers: { "X-Role": rol },
        body: JSON.stringify({
          clave: firma.clave,
          sha256_hash: sha256,
          nombre_archivo: archivo.name,
          tipo_mime: tipo,
          normativa,
        }),
      }
    );
    return { ok: true, evidencia: aEvidencia(confirmada.documento), duplicada: confirmada.duplicada };
  } catch (error) {
    return { ok: false, error: mensajeDeSubida((error as { code?: string }).code, extensiones) };
  }
}

export async function vincularEnServidor(documentoId: string, control: number): Promise<void> {
  await requestJson(`/evidencias/documentos/${encodeURIComponent(documentoId)}/vinculos/${control}`, {
    method: "PUT",
    headers: { "X-Role": ROL_DPO },
  });
}

export async function desvincularEnServidor(documentoId: string, control: number): Promise<void> {
  await requestJson(`/evidencias/documentos/${encodeURIComponent(documentoId)}/vinculos/${control}`, {
    method: "DELETE",
    headers: { "X-Role": ROL_DPO },
  });
}
