// ¤frontend-ide
// ¤rbac-tenant
/**
 * Datos de trabajo guardados en el navegador y quién es su dueño (FE-20).
 *
 * La ficha de la organización, la caché de respuestas, la hoja de ruta abierta, la conversación con
 * el copiloto, la biblioteca de proyectos y el historial de madurez viven en `localStorage`, que es
 * del navegador y no de la persona. Sin dueño, quien entraba después en el mismo navegador veía los
 * datos de otra persona u organización; y si su organización aún no tenía respuestas en el servidor,
 * la caché ajena se subía a ella (`cargarRespuestasDelServidor`).
 *
 * Por eso cada inicio de sesión reclama los datos ANTES de abrir la sesión, que es cuando se
 * sincroniza con el servidor: si son de otra identidad (correo y organización) o de nadie conocido,
 * se vacían en memoria y en el almacenamiento. La misma persona en la misma organización los conserva.
 */
import { useAuditStore } from "./useAuditStore";
import { useCopilotStore } from "./useCopilotStore";
import { useRoadmapStore } from "./useRoadmapStore";

export const CLAVE_DUENO = "lopdp-dueno-datos-v1";
/** Claves sin store propio: los stores se vacían con sus propias acciones. */
const CLAVES_SUELTAS = ["jubys-proyectos-v1"];
const PREFIJOS_SUELTOS = ["lopdp-maturity-history:"];

/** Identidad dueña de los datos: correo (sin mayúsculas) y organización. */
export function duenoDe(email: string, tenant: string): string {
  return `${email.trim().toLowerCase()}|${tenant.trim()}`;
}

/** Vacía los datos de trabajo si no son de `dueno` y lo registra como dueño. Devuelve true si vació. */
export function reclamarDatosDeTrabajo(dueno: string): boolean {
  let almacen: Storage;
  try {
    almacen = window.localStorage;
  } catch {
    return false; // almacenamiento bloqueado: no hay nada guardado que heredar
  }
  if (almacen.getItem(CLAVE_DUENO) === dueno) return false;

  useAuditStore.getState().nuevoProyecto();
  useRoadmapStore.getState().reset();
  useCopilotStore.setState({ sesiones: {} });

  const sueltas: string[] = [];
  for (let i = 0; i < almacen.length; i += 1) {
    const clave = almacen.key(i);
    if (clave && (CLAVES_SUELTAS.includes(clave) || PREFIJOS_SUELTOS.some((p) => clave.startsWith(p)))) {
      sueltas.push(clave);
    }
  }
  sueltas.forEach((clave) => almacen.removeItem(clave));
  almacen.setItem(CLAVE_DUENO, dueno);
  return true;
}
