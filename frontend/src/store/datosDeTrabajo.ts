// ¤frontend-ide
// ¤rbac-tenant
/**
 * Datos de trabajo guardados en el navegador y quién es su dueño (FE-20, ampliado en FE-21).
 *
 * La ficha de la organización, la caché de respuestas, la hoja de ruta abierta, la conversación con
 * el copiloto, la biblioteca de proyectos y el historial de madurez viven en `localStorage`, que es
 * del navegador y no de la persona. El dueño es la pareja correo y organización.
 *
 * Cada inicio de sesión y cada cambio de organización reclaman los datos ANTES de la primera
 * petición a la organización:
 *  - misma persona y misma organización: se conservan;
 *  - misma persona, otra organización: lo de la anterior se guarda aparte para esa persona y se
 *    carga lo que hubiera de la nueva. Un DPO que atiende a varias empresas no pierde la ficha de
 *    cada una, y lo de una organización nunca aparece ni se envía en otra;
 *  - otra persona (o un dueño desconocido): se borra todo, también lo guardado aparte de las demás.
 *
 * Tras reclamar se recarga la página, para que los stores lean lo que quedó en el almacenamiento.
 */
import {
  guardarOrganizacionActiva,
  guardarSesion,
  olvidarCredencialPendiente,
  type Organizacion,
} from "@/lib/auth";
import { abrirProyecto, guardarProyecto } from "@/lib/proyectos";
import { useAuditStore } from "./useAuditStore";
import { useCopilotStore } from "./useCopilotStore";
import { useRoadmapStore } from "./useRoadmapStore";

export const CLAVE_DUENO = "lopdp-dueno-datos-v1";
/** Prefijo de lo guardado aparte por persona y organización: `<prefijo><correo>|<tenant>`. */
export const PREFIJO_GUARDADO = "lopdp-datos-guardados-v1:";
/** Claves que persisten los stores: al vaciarlos quedan con su estado vacío, no se borran. */
const CLAVES_DE_STORES = ["jubys-audit-storage", "lopdp-roadmap-store-v1", "lopdp-copilot-v1"];
/** Claves sin store propio: se borran. */
const CLAVES_SUELTAS = ["jubys-proyectos-v1"];
const PREFIJOS_SUELTOS = ["lopdp-maturity-history:"];

/** Identidad dueña de los datos: correo (sin mayúsculas) y organización. */
export function duenoDe(email: string, tenant: string): string {
  return `${email.trim().toLowerCase()}|${tenant.trim()}`;
}

function correoDe(dueno: string): string {
  return dueno.split("|")[0];
}

function clavesPresentes(almacen: Storage, coincide: (clave: string) => boolean): string[] {
  const claves: string[] = [];
  for (let i = 0; i < almacen.length; i += 1) {
    const clave = almacen.key(i);
    if (clave && coincide(clave)) claves.push(clave);
  }
  return claves;
}

function esSuelta(clave: string): boolean {
  return CLAVES_SUELTAS.includes(clave) || PREFIJOS_SUELTOS.some((p) => clave.startsWith(p));
}

function esDeTrabajo(clave: string): boolean {
  return CLAVES_DE_STORES.includes(clave) || esSuelta(clave);
}

/**
 * Deja los datos de trabajo del navegador listos para `dueno`. Devuelve true si cambió algo.
 * Los stores en memoria se vacían; lo restaurado se lee al recargar la página.
 */
export function reclamarDatosDeTrabajo(dueno: string): boolean {
  let almacen: Storage;
  try {
    almacen = window.localStorage;
  } catch {
    return false; // almacenamiento bloqueado: no hay nada guardado que heredar
  }
  const anterior = almacen.getItem(CLAVE_DUENO);
  if (anterior === dueno) return false;

  if (anterior && correoDe(anterior) === correoDe(dueno)) {
    // La misma persona cambia de organización: lo de la anterior queda guardado aparte.
    const datos: Record<string, string> = {};
    clavesPresentes(almacen, esDeTrabajo).forEach((clave) => {
      datos[clave] = almacen.getItem(clave) ?? "";
    });
    almacen.setItem(PREFIJO_GUARDADO + anterior, JSON.stringify(datos));
  } else {
    // Otra persona: no hereda nada de nadie, tampoco lo guardado aparte de otras personas.
    clavesPresentes(
      almacen,
      (clave) => clave.startsWith(PREFIJO_GUARDADO) && correoDe(clave.slice(PREFIJO_GUARDADO.length)) !== correoDe(dueno)
    ).forEach((clave) => almacen.removeItem(clave));
  }

  // Vaciar los stores deja en sus claves el estado vacío (no el de demostración que tendrían si
  // se borraran); las claves sueltas sí se borran.
  useAuditStore.getState().nuevoProyecto();
  useRoadmapStore.getState().reset();
  useCopilotStore.setState({ sesiones: {} });
  clavesPresentes(almacen, esSuelta).forEach((clave) => almacen.removeItem(clave));

  const guardado = almacen.getItem(PREFIJO_GUARDADO + dueno);
  if (guardado) {
    try {
      Object.entries(JSON.parse(guardado) as Record<string, string>).forEach(([clave, valor]) => {
        if (esDeTrabajo(clave)) almacen.setItem(clave, valor);
      });
    } catch {
      // guardado dañado: la organización arranca vacía
    }
    almacen.removeItem(PREFIJO_GUARDADO + dueno);
  }
  almacen.setItem(CLAVE_DUENO, dueno);
  return true;
}

/**
 * Abre la sesión en una organización: reclama los datos, fija la organización y guarda la sesión
 * sin despertar a nadie, porque quien llama recarga la página a continuación.
 */
export function entrarEnOrganizacion(token: string, email: string, org: Organizacion): boolean {
  reclamarDatosDeTrabajo(duenoDe(email, org.tenant_id));
  guardarOrganizacionActiva(org);
  olvidarCredencialPendiente();
  return guardarSesion(token, { avisar: false });
}

/** Cambia de organización dentro de la misma sesión. Quien llama recarga la página. */
export function cambiarDeOrganizacion(email: string, org: Organizacion): void {
  reclamarDatosDeTrabajo(duenoDe(email, org.tenant_id));
  guardarOrganizacionActiva(org);
}

/**
 * Antes de cambiar de organización con cambios sin guardar: «guardar» los guarda como proyecto de
 * la organización actual; «descartar» vuelve a la última versión guardada (o a un proyecto vacío
 * si nunca se guardó). En ningún caso pasan a la organización nueva. Devuelve false si no se pudo.
 */
export function resolverCambiosSinGuardar(decision: "guardar" | "descartar"): boolean {
  const estado = useAuditStore.getState();
  if (decision === "guardar") {
    const nombre = estado.proyectoActivo?.nombre || estado.companyData.razonSocial || "Proyecto sin nombre";
    const guardado = guardarProyecto(estado.obtenerInstantanea(), nombre, estado.proyectoActivo?.id);
    if (!guardado) return false;
    estado.marcarGuardado({ id: guardado.id, nombre: guardado.nombre });
    return true;
  }
  const ultimo = estado.proyectoActivo ? abrirProyecto(estado.proyectoActivo.id) : null;
  if (ultimo) estado.cargarProyecto(ultimo);
  else estado.nuevoProyecto();
  return true;
}
