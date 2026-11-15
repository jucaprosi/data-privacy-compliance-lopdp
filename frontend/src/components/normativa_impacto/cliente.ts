/**
 * Cliente del análisis de impacto de una resolución (NORM-03). La organización y la persona salen de la sesión;
 * el servidor autoriza cada llamada: pide el análisis la administración o el DPO, y decide solo el DPO.
 */
import { cabecerasDeMiembro } from "@/lib/auth/cabeceras";
import { fetchAutenticado } from "@/lib/auth/fetchAutenticado";

const BASE = "/api/v1/normativa";

export const ROLES_PEDIDO = ["dpo", "admin_organizacion"] as const;
export const ROLES_DECISION = ["dpo"] as const;

export type TipoElemento = "pregunta" | "tratamiento" | "tarea" | "plantilla";
export type EstadoImpacto = "propuesta" | "aceptada" | "rechazada";

export interface ElementoImpacto {
  tipo: TipoElemento;
  referencia_id: string;
  motivo: string;
  articulos_citados: string[];
}
export interface AnalisisImpacto {
  id: string;
  resolucion_id: string;
  modelo: string;
  propuesta: ElementoImpacto[];
  sin_base_normativa: boolean;
  estado: EstadoImpacto;
  creada_en: string;
  decidida_en: string | null;
  nota: string | null;
  hallazgos_generados: number;
}

export class ErrorImpacto extends Error {
  constructor(readonly status: number, readonly codigo?: string) {
    super(codigo ?? `HTTP ${status}`);
  }
}

async function pedir(ruta: string, roles: readonly string[], init: RequestInit = {}): Promise<Response> {
  const respuesta = await fetchAutenticado(
    `${BASE}${ruta}`,
    { ...init, headers: { "Content-Type": "application/json", ...(init.headers ?? {}) } },
    cabecerasDeMiembro(roles),
  );
  if (!respuesta.ok) {
    let codigo: string | undefined;
    try {
      const cuerpo = (await respuesta.json()) as { detail?: { codigo?: string } };
      codigo = cuerpo?.detail?.codigo;
    } catch {
      // El texto del servidor nunca se muestra: solo su código.
    }
    throw new ErrorImpacto(respuesta.status, codigo);
  }
  return respuesta;
}

export async function listarImpactos(resolucionId: string): Promise<AnalisisImpacto[]> {
  const p = new URLSearchParams({ resolucion_id: resolucionId });
  return (await pedir(`/impacto?${p}`, [])).json();
}
export async function pedirAnalisis(resolucionId: string): Promise<AnalisisImpacto> {
  return (await pedir(`/resoluciones/${encodeURIComponent(resolucionId)}/impacto`, ROLES_PEDIDO, { method: "POST" })).json();
}
export async function decidirImpacto(id: string, decision: "aceptar" | "rechazar", nota: string): Promise<AnalisisImpacto> {
  return (await pedir(`/impacto/${encodeURIComponent(id)}/decision`, ROLES_DECISION, {
    method: "POST", body: JSON.stringify({ decision, nota }),
  })).json();
}
