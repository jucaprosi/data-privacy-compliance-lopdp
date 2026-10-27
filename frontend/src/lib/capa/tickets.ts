/**
 * Cliente HTTP tipado para la sala de Auditoría y Planes de Acción (CAPA-01).
 * Utiliza exclusivamente fetchAutenticado sin modificar frontend/src/lib/api.ts.
 */
import { cabecerasDeRol, cabecerasDeTenant, fetchAutenticado } from "@/lib/auth";

export type SeveridadHallazgoCAPA =
  | "OBSERVACION"
  | "NO_CONFORMIDAD_MENOR"
  | "NO_CONFORMIDAD_MAYOR"
  | "VULNERABILIDAD_CRITICA";

export type EstadoTicketCAPA =
  | "ABIERTO"
  | "EN_REMEDIACION"
  | "PENDIENTE_VERIFICACION"
  | "CERRADO_VERIFICADO";

export interface TicketCAPAPersistido {
  id: string;
  tenant_id: string;
  control_id: string;
  severidad: SeveridadHallazgoCAPA | string;
  descripcion_hallazgo: string;
  causa_raiz: string;
  accion_correctiva: string;
  responsable_implementacion_id: string;
  creado_por?: string;
  auditor_verificador_id?: string | null;
  estado: EstadoTicketCAPA | string;
  evidencia_cierre_id?: string | null;
  fecha_creacion?: string | null;
  fecha_cierre?: string | null;
}

export interface CrearTicketCAPAPayload {
  control_id: string;
  severidad: SeveridadHallazgoCAPA | string;
  descripcion_hallazgo: string;
  causa_raiz: string;
  accion_correctiva: string;
  responsable_implementacion_id: string;
}

export interface ContextoUsuarioCapa {
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

export async function obtenerContextoRolesCapa(): Promise<ContextoUsuarioCapa> {
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

export async function listarTicketsCapa(
  rol?: string,
  userId?: string,
): Promise<TicketCAPAPersistido[]> {
  const res = await fetchAutenticado("/api/v1/capa/tickets", {
    method: "GET",
    headers: construirCabeceras(rol, userId),
  });
  if (!res.ok) {
    throw await extraerError(res, "No se pudieron cargar los tickets CAPA.");
  }
  const data = (await res.json()) as TicketCAPAPersistido[] | { tickets?: TicketCAPAPersistido[] };
  if (Array.isArray(data)) {
    return data;
  }
  return Array.isArray(data?.tickets) ? data.tickets : [];
}

export async function crearTicketCapa(
  payload: CrearTicketCAPAPayload,
  rol = "coordinador",
  userId?: string,
): Promise<TicketCAPAPersistido> {
  const res = await fetchAutenticado("/api/v1/capa/tickets", {
    method: "POST",
    headers: construirCabeceras(rol, userId),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw await extraerError(res, "No se pudo registrar el hallazgo CAPA.");
  }
  return (await res.json()) as TicketCAPAPersistido;
}

export async function cerrarTicketCapa(
  ticketId: string,
  evidenciaId: string,
  rol = "coordinador",
  userId?: string,
): Promise<TicketCAPAPersistido> {
  const res = await fetchAutenticado(
    `/api/v1/capa/tickets/${encodeURIComponent(ticketId)}/cerrar`,
    {
      method: "POST",
      headers: construirCabeceras(rol, userId),
      body: JSON.stringify({ evidencia_id: evidenciaId }),
    },
  );
  if (!res.ok) {
    throw await extraerError(res, "No se pudo verificar y cerrar el hallazgo CAPA.");
  }
  return (await res.json()) as TicketCAPAPersistido;
}
