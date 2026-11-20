// ¤api-integraciones ¤frontend-ide
/**
 * Cliente HTTP para suscripciones de webhooks firmados (API-02b).
 *
 * Usa fetchAutenticado y cabeceras de identidad; nunca propaga textos de error del servidor
 * ni almacena secretos fuera del estado transitorio de la pantalla.
 */
import { cabecerasDeRol, fetchAutenticado, leerOrganizacionActiva, modoAutenticacion } from "@/lib/auth";

export interface WebhookSuscripcion {
  id: string;
  url: string;
  eventos: string[];
  activo: boolean;
  creada_en: string;
  rotada_en: string | null;
}

export interface WebhookConSecretoResponse {
  status: string;
  webhook: WebhookSuscripcion;
  secreto_en_claro: string;
}

export interface ResultadoPruebaWebhook {
  entregado: boolean;
  intentos: number;
  estado_http: number | null;
}

export interface TechosWebhooksResumen {
  maximo: number | null;
  activos: number;
}

export const NOMBRES_EVENTOS_WEBHOOK: Readonly<Record<string, string>> = {
  "webhook.prueba": "Aviso de prueba",
  "incidente.registrado": "Incidente registrado",
  "derecho.solicitud_recibida": "Solicitud de un titular recibida",
  "tarea.validada": "Tarea de la hoja de ruta con validación final",
};

/** Solo se ofrecen los eventos con una sala emisora activa en esta ficha. */
export const EVENTOS_CON_EMISORA: readonly string[] = ["webhook.prueba"];

export function nombreEventoWebhook(codigo: string): string {
  return NOMBRES_EVENTOS_WEBHOOK[codigo] ?? "Aviso del sistema";
}

export class ErrorWebhookApi extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string | null,
  ) {
    super(code || `HTTP_${status}`);
    this.name = "ErrorWebhookApi";
  }
}

function cabecerasAdmin(): Record<string, string> {
  const orgActiva = leerOrganizacionActiva();
  if (orgActiva && orgActiva.roles.length > 0 && !orgActiva.roles.includes("admin_organizacion")) {
    throw new ErrorWebhookApi(403, "FORBIDDEN");
  }
  const usuarioDev = process.env.NEXT_PUBLIC_USER_ID || "user-demo-admin";
  const base = cabecerasDeRol("admin_organizacion", usuarioDev);
  if (modoAutenticacion() === "headers" && !base["X-User-ID"]) {
    base["X-User-ID"] = usuarioDev;
  }
  return base;
}

async function leerCodigoError(res: Response): Promise<string | null> {
  const cuerpo = (await res.json().catch(() => null)) as
    | { code?: unknown; detail?: { code?: unknown } }
    | null;
  if (typeof cuerpo?.code === "string") return cuerpo.code;
  if (cuerpo?.detail && typeof cuerpo.detail === "object" && typeof cuerpo.detail.code === "string") {
    return cuerpo.detail.code;
  }
  return null;
}

async function pedirWebhook<T>(url: string, init: RequestInit = {}): Promise<T> {
  const cabeceras = cabecerasAdmin();
  const res = await fetchAutenticado(url, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...cabeceras,
      ...((init.headers ?? {}) as Record<string, string>),
    },
  });
  if (!res.ok) {
    const code = await leerCodigoError(res);
    throw new ErrorWebhookApi(res.status, code);
  }
  return (await res.json()) as T;
}

export async function listarWebhooks(): Promise<WebhookSuscripcion[]> {
  const data = await pedirWebhook<{ webhooks?: WebhookSuscripcion[] }>("/api/v1/integraciones/webhooks", {
    method: "GET",
  });
  return Array.isArray(data.webhooks) ? data.webhooks : [];
}

export async function obtenerTechosWebhooks(): Promise<TechosWebhooksResumen | null> {
  try {
    const cabeceras = cabecerasAdmin();
    const res = await fetchAutenticado("/api/v1/integraciones/techos", {
      method: "GET",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...cabeceras,
      },
    });
    if (!res.ok) return null;
    const data = (await res.json()) as { webhooks?: TechosWebhooksResumen };
    if (!data?.webhooks) return null;
    return {
      maximo: data.webhooks.maximo ?? null,
      activos: Number(data.webhooks.activos ?? 0),
    };
  } catch {
    return null;
  }
}

export async function crearWebhook(url: string, eventos: string[]): Promise<WebhookConSecretoResponse> {
  return pedirWebhook<WebhookConSecretoResponse>("/api/v1/integraciones/webhooks", {
    method: "POST",
    body: JSON.stringify({ url, eventos }),
  });
}

export async function rotarSecretoWebhook(id: string): Promise<WebhookConSecretoResponse> {
  return pedirWebhook<WebhookConSecretoResponse>(
    `/api/v1/integraciones/webhooks/${encodeURIComponent(id)}/rotar-secreto`,
    { method: "POST" },
  );
}

export async function desactivarWebhook(id: string): Promise<WebhookSuscripcion> {
  const data = await pedirWebhook<{ webhook: WebhookSuscripcion }>(
    `/api/v1/integraciones/webhooks/${encodeURIComponent(id)}/desactivar`,
    { method: "POST" },
  );
  return data.webhook;
}

export async function probarWebhook(id: string): Promise<ResultadoPruebaWebhook> {
  return pedirWebhook<ResultadoPruebaWebhook>(
    `/api/v1/integraciones/webhooks/${encodeURIComponent(id)}/probar`,
    { method: "POST" },
  );
}
