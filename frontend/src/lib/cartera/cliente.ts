/**
 * Cliente de la cartera de organizaciones (ORG-15). ¤cartera
 *
 * Forma de la respuesta, tomada de `features/organizacion/services/cartera_engine.py` y de
 * governance/especificaciones/ORG-15.md §2: `GET /organizacion/cartera` → `{organizaciones: [FilaCartera]}`.
 * La lista sale de las organizaciones donde la persona tiene un rol vigente; la identidad viaja en el
 * token. La fila lleva las dimensiones por separado y contadores, nunca un puntaje único.
 */
import { fetchAutenticado } from "@/lib/auth/fetchAutenticado";

export const RUTA_CARTERA = "/api/v1/organizacion/cartera";

export interface NivelDimension {
  dimension: string;
  nivel: number;
}

export interface DiagnosticoCartera {
  escala: string | null;
  niveles_por_dimension: NivelDimension[];
  cumplimiento: boolean;
  /** Describe el respaldo documental, no la madurez; no se muestra como cifra. */
  respaldo_documental: number;
  brechas_criticas: number;
  brechas_altas: number;
  sellado_en: string;
}

export interface FilaCartera {
  tenant_id: string;
  nombre: string;
  roles: string[];
  diagnostico: DiagnosticoCartera | null;
  hallazgos_abiertos: number | null;
  tareas_vencidas: number | null;
  cadena_integra: boolean | null;
  /** `SIN_DATOS` cuando el servidor no pudo calcular los indicadores de esta organización. */
  error?: string;
}

function esFila(valor: unknown): valor is FilaCartera {
  const f = valor as FilaCartera | null;
  return Boolean(f && typeof f.tenant_id === "string" && f.tenant_id && typeof f.nombre === "string" && Array.isArray(f.roles));
}

export async function consultarCartera(): Promise<FilaCartera[]> {
  const respuesta = await fetchAutenticado(RUTA_CARTERA, { headers: { Accept: "application/json" }, cache: "no-store" });
  if (!respuesta.ok) throw new Error(`el servidor respondió ${respuesta.status}`);
  const cuerpo = (await respuesta.json()) as { organizaciones?: unknown[] };
  return (cuerpo.organizaciones ?? []).filter(esFila);
}
