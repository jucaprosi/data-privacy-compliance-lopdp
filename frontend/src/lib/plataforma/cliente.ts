import { cabecerasDePlataforma } from "@/lib/auth/cabeceras";
import { fetchAutenticado } from "@/lib/auth/fetchAutenticado";

import type {
  AceptacionInvitacion,
  AltaOrganizacion,
  ErrorApiPlataforma,
  OrganizacionCrear,
  OrganizacionResumen,
} from "./tipos";

const BASE = "/api/v1/plataforma";

export class ErrorPlataforma extends Error {
  constructor(
    readonly status: number,
    mensaje: string,
    readonly codigo?: string,
  ) {
    super(mensaje);
    this.name = "ErrorPlataforma";
  }
}

async function solicitar<T>(ruta: string, init: RequestInit = {}): Promise<T> {
  // Como el resto de clientes: un 401 cierra la sesión caducada (fetchAutenticado).
  const respuesta = await fetchAutenticado(
    `${BASE}${ruta}`,
    { ...init, headers: { "Content-Type": "application/json", ...(init.headers ?? {}) } },
    cabecerasDePlataforma(),
  );
  if (!respuesta.ok) {
    let error: ErrorApiPlataforma = {};
    try {
      error = (await respuesta.json()) as ErrorApiPlataforma;
    } catch {
      // Una respuesta no JSON conserva el mensaje seguro por estado.
    }
    throw new ErrorPlataforma(
      respuesta.status,
      error.detail || `La operación no pudo completarse (${respuesta.status}).`,
      error.code,
    );
  }
  return (await respuesta.json()) as T;
}

export const plataformaApi = {
  listar: () => solicitar<OrganizacionResumen[]>("/organizaciones"),
  crear: (datos: OrganizacionCrear) =>
    solicitar<AltaOrganizacion>("/organizaciones", {
      method: "POST",
      body: JSON.stringify(datos),
    }),
  reemitir: (tenantId: string, emailAdminInicial?: string) =>
    solicitar<AltaOrganizacion>(
      `/organizaciones/${encodeURIComponent(tenantId)}/invitaciones`,
      {
        method: "POST",
        body: JSON.stringify(
          emailAdminInicial ? { email_admin_inicial: emailAdminInicial } : {},
        ),
      },
    ),
  revocar: (invitacionId: string) =>
    solicitar<{ status: string; mensaje: string }>(`/invitaciones/${encodeURIComponent(invitacionId)}/revocar`, {
      method: "POST",
    }),
  aceptar: (codigo: string, nombreUsuario?: string) =>
    solicitar<AceptacionInvitacion>("/invitaciones/aceptar", {
      method: "POST",
      body: JSON.stringify({ codigo, nombre_usuario: nombreUsuario?.trim() || null }),
    }),
};

// === ORG-21 ===
/**
 * ¿La persona de este token es operadora de la plataforma? Lo decide el servidor: se pregunta con
 * `Authorization: Bearer <token>` a una ruta que ya exige operador (`verificar_operador`).
 * 200 ⟹ sí; 403 ⟹ no; cualquier otro estado se propaga como `ErrorPlataforma`.
 *
 * Se usa en la pantalla de entrada, antes de que exista la sesión: por eso el token va explícito y
 * no pasa por `fetchAutenticado`, que cerraría una sesión que todavía no hay. Solo decide a dónde
 * llevar a la persona; la autoridad sigue en el servidor, en cada ruta de `/api/v1/plataforma`.
 */
export async function esOperadorDeLaPlataforma(token: string): Promise<boolean> {
  const respuesta = await fetch(`${BASE}/organizaciones`, { headers: { Authorization: `Bearer ${token}` } });
  if (respuesta.ok) return true;
  if (respuesta.status === 403) return false;
  throw new ErrorPlataforma(respuesta.status, `La plataforma respondió ${respuesta.status}.`);
}
// === fin ORG-21 ===

export type {
  AceptacionInvitacion,
  AltaOrganizacion,
  OrganizacionCrear,
  OrganizacionResumen,
  TamanoOrganizacion,
} from "./tipos";
