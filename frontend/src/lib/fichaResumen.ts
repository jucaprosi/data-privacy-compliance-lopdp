/**
 * Datos de la ficha resumen de la organización (FE-25). ¤frontend-ide ¤tablero-dimensiones
 *
 * No calcula nada: toma la fila de la organización activa de `GET /organizacion/cartera` (ORG-15) y la
 * presenta. Sin cifra única (INV_LOPDP_MULTIDIMENSIONAL_METRICS): las cuatro dimensiones van por separado.
 * Faltan en la fila de la cartera, y por eso la ficha todavía no los muestra: RUC, naturaleza,
 * nombre del DPO y del consultor, y los plazos de solicitudes y vulneraciones.
 */
import { fetchAutenticado } from "@/lib/auth/fetchAutenticado";
import { consultarCartera, type FilaCartera } from "@/lib/cartera/cliente";
import { tarjetasDeFila } from "@/lib/cartera/semaforos";
import { claveDeEtiqueta, infoDeTamano } from "@/lib/tamanoOrganizacion";
import type { TarjetaDimension } from "@/lib/tableros/resumen";

/** Etiqueta legible del tamaño («Microempresa»), no el valor interno de la ficha. */
export const etiquetaTamano = (tamano: string): string => infoDeTamano(claveDeEtiqueta(tamano)).etiqueta;

export interface FichaResumenDatos {
  nombre: string;
  sector: string;
  tamano: string;
  dpo: string | null;
  consultor: string | null;
  tareasVencidas: number | null;
  hallazgosAbiertos: number | null;
  /** Cuatro tarjetas por dimensión, o `null` si no hay diagnóstico sellado. */
  dimensiones: TarjetaDimension[] | null;
}

export interface Designaciones {
  dpo: string | null;
  consultor: string | null;
}

/**
 * Nombre del DPO y del consultor vigentes. `GET /organizacion/roles` solo lo lee el administrador, así que
 * no se usa; la fuente será la ampliación de la fila de la cartera (`dpo_nombre`, `implementador_nombre`).
 * Mientras tanto devuelve `null` y la ficha no escribe ese dato (nunca «Sin designar»).
 */
export async function cargarDesignaciones(): Promise<Designaciones> {
  return { dpo: null, consultor: null };
}

/** Fila de la organización activa; `undefined` si la cartera no la trae. */
export function filaDeLaActiva(filas: readonly FilaCartera[], tenantActivo: string): FilaCartera | undefined {
  return filas.find((f) => f.tenant_id === tenantActivo);
}

export function datosDeFicha(
  fila: FilaCartera,
  contexto: { sector: string; tamano: string },
  designaciones: Designaciones,
): FichaResumenDatos {
  return {
    nombre: fila.nombre,
    sector: contexto.sector,
    tamano: etiquetaTamano(contexto.tamano),
    dpo: designaciones.dpo,
    consultor: designaciones.consultor,
    tareasVencidas: fila.error === "SIN_DATOS" ? null : fila.tareas_vencidas,
    hallazgosAbiertos: fila.error === "SIN_DATOS" ? null : fila.hallazgos_abiertos,
    dimensiones: fila.error === "SIN_DATOS" ? null : tarjetasDeFila(fila),
  };
}

async function tieneRolesVigentes(): Promise<boolean> {
  const respuesta = await fetchAutenticado("/api/v1/organizacion/me/roles", { headers: { Accept: "application/json" }, cache: "no-store" });
  if (!respuesta.ok) return false;
  const cuerpo = (await respuesta.json()) as { roles?: unknown[] };
  return Array.isArray(cuerpo.roles) && cuerpo.roles.length > 0;
}

export async function cargarFicha(
  tenantActivo: string,
  contexto: { sector: string; tamano: string },
): Promise<FichaResumenDatos | null> {
  // Sin roles confirmados no se pide nada más de la organización (misma regla que la Hoja de Ruta).
  if (!(await tieneRolesVigentes())) throw new Error("sin roles confirmados");
  const [filas, designaciones] = await Promise.all([consultarCartera(), cargarDesignaciones()]);
  const fila = filaDeLaActiva(filas, tenantActivo);
  return fila ? datosDeFicha(fila, contexto, designaciones) : null;
}
