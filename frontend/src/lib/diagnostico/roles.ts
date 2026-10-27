/**
 * Quién responde, sella y consulta el diagnóstico (DIAG-03).
 *
 * Solo el DPO responde y sella; implementador, coordinador y administrador consultan. Los roles se
 * leen de /organizacion/me/roles, que el servidor resuelve con la identidad verificada. Si esa
 * consulta falla, se usa el rol de la sesión del cliente: el servidor lo vuelve a comprobar en
 * cada llamada, así que un rol mal supuesto solo produce un 403, nunca un permiso de más.
 */
import { cabecerasDeRol, suscribirSesion, type CabecerasIdentidad } from "@/lib/auth";
import { getCurrentSession, organizacionApi } from "@/lib/roadmap/cliente";

export const ROL_QUE_SELLA = "dpo";
export const ROLES_QUE_CONSULTAN = ["dpo", "implementador", "coordinador", "admin_organizacion"] as const;

let pendiente: Promise<string[]> | null = null;
let resueltos: string[] | null = null;

if (typeof window !== "undefined") {
  // Otra persona (u otra organización) no hereda los roles de la anterior.
  suscribirSesion(() => {
    pendiente = null;
    resueltos = null;
  });
}

/** Roles vigentes del usuario en la organización activa. */
export function rolesDelUsuario(): Promise<string[]> {
  if (!pendiente) {
    pendiente = organizacionApi
      .getMyRoles()
      .then((roles) => {
        resueltos = roles.map((r) => r.role as string);
        return resueltos;
      })
      .catch(() => {
        pendiente = null;
        const rol = getCurrentSession().role;
        return rol ? [rol] : [];
      });
  }
  return pendiente;
}

export function puedeSellar(roles: readonly string[]): boolean {
  return roles.includes(ROL_QUE_SELLA);
}

/** El primer rol con el que el usuario puede consultar, o null si ninguno lo permite. */
export function rolParaConsultar(roles: readonly string[]): string | null {
  return ROLES_QUE_CONSULTAN.find((rol) => roles.includes(rol)) ?? null;
}

/**
 * Rol con el que leer. Si la sesión ya declara un rol que consulta, se usa sin preguntar al
 * servidor: así la carga inicial de la ficha no llama a Organización (FE-08). Si no (por ejemplo,
 * el rol por defecto de una sesión de Google), se consultan los roles reales.
 */
export async function rolParaLeer(): Promise<string | null> {
  if (resueltos) return rolParaConsultar(resueltos);
  const declarado = getCurrentSession().role as string;
  if ((ROLES_QUE_CONSULTAN as readonly string[]).includes(declarado)) return declarado;
  return rolParaConsultar(await rolesDelUsuario());
}

/** Cabeceras de identidad declarando el rol con el que se actúa (el servidor lo verifica). */
export function cabecerasComo(rol: string): CabecerasIdentidad {
  const sesion = getCurrentSession();
  const cabeceras = cabecerasDeRol(rol, sesion.userId);
  if (sesion.tenantId) cabeceras["X-Tenant-ID"] = sesion.tenantId;
  return cabeceras;
}
