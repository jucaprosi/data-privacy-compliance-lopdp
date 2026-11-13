/**
 * Datos de la ficha resumen de la organización (FE-25). ¤frontend-ide ¤tablero-dimensiones
 *
 * No calcula nada: toma la fila de la organización activa de `GET /organizacion/cartera` (ORG-15) y la
 * presenta. Sin cifra única (INV_LOPDP_MULTIDIMENSIONAL_METRICS): las cuatro dimensiones van por separado.
 * Faltan en la fila de la cartera, y por eso la ficha muestra «—» en su lugar: RUC, naturaleza, sector,
 * tamaño, nombre del DPO y del consultor, y los plazos de solicitudes y vulneraciones. No se leen del
 * store: la ficha solo presenta lo que el servidor envía.
 */
import { organizacionApi } from "@/lib/roadmap/cliente";
import { consultarCartera, type FilaCartera } from "@/lib/cartera/cliente";
import { tarjetasDeFila } from "@/lib/cartera/semaforos";
import type { TarjetaDimension } from "@/lib/tableros/resumen";

export interface FichaResumenDatos {
  nombre: string;
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
  designaciones: Designaciones,
): FichaResumenDatos {
  return {
    nombre: fila.nombre,
    dpo: designaciones.dpo,
    consultor: designaciones.consultor,
    tareasVencidas: fila.error === "SIN_DATOS" ? null : fila.tareas_vencidas,
    hallazgosAbiertos: fila.error === "SIN_DATOS" ? null : fila.hallazgos_abiertos,
    dimensiones: fila.error === "SIN_DATOS" ? null : tarjetasDeFila(fila),
  };
}

async function tieneRolesVigentes(): Promise<boolean> {
  try {
    return (await organizacionApi.getMyRoles()).length > 0;
  } catch {
    return false;
  }
}

export async function cargarFicha(tenantActivo: string): Promise<FichaResumenDatos | null> {
  // Sin roles confirmados no se pide nada más de la organización (misma regla que la Hoja de Ruta).
  if (!(await tieneRolesVigentes())) throw new Error("sin roles confirmados");
  const [filas, designaciones] = await Promise.all([consultarCartera(), cargarDesignaciones()]);
  const fila = filaDeLaActiva(filas, tenantActivo);
  return fila ? datosDeFicha(fila, designaciones) : null;
}
