/**
 * Cliente HTTP tipado para el Cockpit DPD/DPO y la Bitácora Inviolable (DPO-01).
 * Utiliza exclusivamente fetchAutenticado sin modificar frontend/src/lib/api.ts.
 */
import { cabecerasDeRol, cabecerasDeTenant, fetchAutenticado } from "@/lib/auth";

export type TipoDictamenDPO =
  | "OPINION_CONSULTIVA"
  | "ADVERTENCIA_RIESGO"
  | "RECOMENDACION_EIPD"
  | "DICTAMEN_TRANSFERENCIA"
  | "AUDITORIA_INFORME"
  | "ALERTA_RIESGO_GRAVE"
  | "VALIDACION_EIPD";

export interface DictamenBitacoraDPO {
  id: string;
  tenant_id?: string;
  dpo_id: string;
  tipo: TipoDictamenDPO | string;
  asunto: string;
  referencia_normativa: string;
  cuerpo: string;
  fecha_emision?: string;
  es_vinculante?: boolean;
  prev_hash?: string;
  sha256_hash?: string;
  acuse_recibo_alta_direccion?: boolean;
  acuse_por?: string | null;
  fecha_acuse?: string | null;
}

export interface EmitirDictamenPayload {
  tipo: TipoDictamenDPO | string;
  asunto: string;
  referencia_normativa: string;
  cuerpo: string;
}

export interface ContextoUsuarioDpo {
  user_id: string;
  tenant_id: string;
  roles: string[];
}

function construirCabeceras(rol?: string, userId?: string): Record<string, string> {
  if (rol) {
    return {
      "Content-Type": "application/json",
      ...cabecerasDeRol(rol, userId || ""),
    };
  }
  return {
    "Content-Type": "application/json",
    ...cabecerasDeTenant(),
  };
}

async function extraerError(res: Response, mensajePorDefecto: string): Promise<Error> {
  const cuerpo = (await res.json().catch(() => null)) as { detail?: unknown } | null;
  const detalle =
    typeof cuerpo?.detail === "string"
      ? cuerpo.detail
      : res.statusText || mensajePorDefecto;
  return new Error(`HTTP ${res.status}: ${detalle}`);
}

export async function obtenerContextoRolesDpo(): Promise<ContextoUsuarioDpo> {
  const res = await fetchAutenticado("/api/v1/organizacion/me/roles", {
    method: "GET",
    headers: construirCabeceras(),
  });
  if (!res.ok) {
    throw await extraerError(res, "No se pudo consultar el perfil del usuario.");
  }
  const data = (await res.json()) as
    | {
        user_id?: string;
        tenant_id?: string;
        roles?: Array<{ role?: string; valid_to?: string | null } | string>;
      }
    | Array<{ role?: string; valid_to?: string | null }>;

  if (Array.isArray(data)) {
    const roles = data
      .filter((r) => !r.valid_to)
      .map((r) => r.role ?? "")
      .filter(Boolean);
    return { user_id: "", tenant_id: "", roles };
  }

  const listaRoles = Array.isArray(data.roles)
    ? data.roles
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && !item.valid_to && typeof item.role === "string") return item.role;
          return "";
        })
        .filter(Boolean)
    : [];

  return {
    user_id: data.user_id ?? "",
    tenant_id: data.tenant_id ?? "",
    roles: listaRoles,
  };
}

export async function listarBitacoraDpo(
  rol?: string,
  userId?: string,
): Promise<DictamenBitacoraDPO[]> {
  const res = await fetchAutenticado("/api/v1/dpo/bitacora", {
    method: "GET",
    headers: construirCabeceras(rol, userId),
  });
  if (!res.ok) {
    throw await extraerError(res, "No se pudo cargar la bitácora.");
  }
  const data = (await res.json()) as { dictamenes?: DictamenBitacoraDPO[] };
  return Array.isArray(data.dictamenes) ? data.dictamenes : [];
}

export async function emitirDictamenDpo(
  payload: EmitirDictamenPayload,
  rol = "dpo",
  userId?: string,
): Promise<DictamenBitacoraDPO> {
  const res = await fetchAutenticado("/api/v1/dpo/dictamenes", {
    method: "POST",
    headers: construirCabeceras(rol, userId),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw await extraerError(res, "No se pudo emitir el dictamen en la bitácora.");
  }
  const data = (await res.json()) as { dictamen: DictamenBitacoraDPO };
  return data.dictamen;
}

export async function firmarAcuseDictamenDpo(
  dictamenId: string,
  rol = "admin_organizacion",
  userId?: string,
): Promise<DictamenBitacoraDPO> {
  const res = await fetchAutenticado(
    `/api/v1/dpo/dictamenes/${encodeURIComponent(dictamenId)}/acuse`,
    {
      method: "POST",
      headers: construirCabeceras(rol, userId),
    },
  );
  if (!res.ok) {
    throw await extraerError(res, "No se pudo registrar el acuse de recibo.");
  }
  const data = (await res.json()) as { dictamen: DictamenBitacoraDPO };
  return data.dictamen;
}
