/**
 * Quién registra y quién consulta la bitácora de incidentes (INC-01).
 *
 * Registran el administrador, el coordinador, los responsables de área y el implementador;
 * consulta además el DPO. Los roles se leen de /organizacion/me/roles solo cuando se abre el
 * módulo, nunca al cargar la ficha (FE-08). Si esa consulta falla, se usa el rol de la sesión del
 * cliente: el servidor lo vuelve a comprobar en cada llamada, así que un rol mal supuesto solo
 * produce un 403.
 */
import { cabecerasDeRol, suscribirSesion, type CabecerasIdentidad } from "@/lib/auth";
import { getCurrentSession, organizacionApi } from "@/lib/roadmap/cliente";

export const ROLES_QUE_REGISTRAN = ["admin_organizacion", "coordinador", "responsable_area", "implementador"] as const;
export const ROLES_QUE_CONSULTAN = [...ROLES_QUE_REGISTRAN, "dpo"] as const;

let pendiente: Promise<string[]> | null = null;

if (typeof window !== "undefined") {
  // Otra persona (u otra organización) no hereda los roles de la anterior.
  suscribirSesion(() => {
    pendiente = null;
  });
}

/** Roles vigentes del usuario en la organización activa. */
export function rolesDelUsuario(): Promise<string[]> {
  if (!pendiente) {
    pendiente = organizacionApi
      .getMyRoles()
      .then((roles) => roles.map((r) => r.role as string))
      .catch(() => {
        pendiente = null;
        const rol = getCurrentSession().role as string;
        return rol ? [rol] : [];
      });
  }
  return pendiente;
}

/** El primero de los roles del usuario que está entre los permitidos, o null. */
export function rolEntre(roles: readonly string[], permitidos: readonly string[]): string | null {
  return permitidos.find((rol) => roles.includes(rol)) ?? null;
}

/** Cabeceras de identidad declarando el rol con el que se actúa (el servidor lo verifica). */
export function cabecerasComo(rol: string): CabecerasIdentidad {
  const sesion = getCurrentSession();
  const cabeceras = cabecerasDeRol(rol, sesion.userId);
  if (sesion.tenantId) cabeceras["X-Tenant-ID"] = sesion.tenantId;
  return cabeceras;
}
