/**
 * Cabeceras de identidad: el único sitio donde el frontend decide qué identidad envía.
 *
 * Todos los clientes de la API las piden aquí (roadmap, preanálisis, bóveda de evidencias, ARCO,
 * terceros, mitigación...). Ninguno lleva ya un usuario, un tenant ni un token fijos en el código.
 *
 *  - "oidc": `Authorization: Bearer <token de Google>` + `X-Tenant-ID`. No se envía X-User-ID: el
 *    servidor lo ignoraría, y mandarlo sugeriría que cuenta.
 *  - "headers" (solo desarrollo): `X-Tenant-ID`, y para roadmap además `X-User-ID` y `X-Role`.
 *
 * Biblioteca declara además el rol con `cabecerasDeMiembro` (BIB-115): sus rutas lo exigen siempre.
 */
import { modoAutenticacion, tenantConfigurado } from "./modo";
import { leerOrganizacionActiva } from "./organizacion";
import { leerSesion } from "./sesion";

export type CabecerasIdentidad = Record<string, string>;

/** Para los endpoints que solo necesitan saber la organización. */
export function cabecerasDeTenant(): CabecerasIdentidad {
  const cabeceras: CabecerasIdentidad = {};
  const tenant = tenantConfigurado();
  if (tenant) cabeceras["X-Tenant-ID"] = tenant;
  if (modoAutenticacion() === "oidc") {
    const sesion = leerSesion();
    if (sesion) cabeceras.Authorization = `Bearer ${sesion.token}`;
  }
  return cabeceras;
}

/**
 * Para Hoja de Ruta y Organización, que además declaran el rol con el que se actúa. El servidor
 * autoriza ese rol contra la membresía del usuario verificado.
 *
 * `usuarioDeDesarrollo` solo se usa en modo "headers".
 */
export function cabecerasDeRol(rol: string, usuarioDeDesarrollo: string): CabecerasIdentidad {
  const cabeceras: CabecerasIdentidad = { ...cabecerasDeTenant(), "X-Role": rol };
  if (modoAutenticacion() === "headers") cabeceras["X-User-ID"] = usuarioDeDesarrollo;
  return cabeceras;
}

// ¤rbac-tenant (BIB-115)
/**
 * Preferencia al elegir rol cuando la ruta admite a cualquier miembro (`get_context` en
 * `api/rbac.py`). Solo ordena: el servidor vuelve a autorizar el rol contra la membresía.
 */
const PREFERENCIA_DE_ROL = ["coordinador", "admin_organizacion", "implementador", "dpo", "responsable_area"];

const NOMBRE_DE_ROL: Record<string, string> = {
  admin_organizacion: "administración de la organización",
  coordinador: "coordinación",
  dpo: "delegado de protección de datos",
  implementador: "implementación",
  responsable_area: "responsable de área",
};

/** El usuario no tiene en la organización activa ningún rol que la operación admita. No se envía nada. */
export class SinRolPermitido extends Error {
  constructor(public readonly rolesPermitidos: readonly string[]) {
    super(
      rolesPermitidos.length
        ? `Tu rol en esta organización no permite esta operación. Se necesita: ${rolesPermitidos
            .map((rol) => NOMBRE_DE_ROL[rol] ?? rol)
            .join(", ")}.`
        : "No tienes un rol activo en la organización seleccionada.",
    );
    this.name = "SinRolPermitido";
  }
}

/** Usuario y rol que declara el modo "headers" (desarrollo); ver `PRUEBAS_EN_FISICO.md`. */
function identidadDeDesarrollo(): { usuario: string; rol: string } {
  return {
    usuario: process.env.NEXT_PUBLIC_USER_ID || "user-demo-implementador",
    rol: process.env.NEXT_PUBLIC_USER_ROLE || "implementador",
  };
}

/**
 * Rol declarado. Con organización activa, sus roles (los verificó el servidor al iniciar sesión): se
 * toma el primero permitido, o el de mayor preferencia. Sin ella, en modo "headers" (desarrollo) el
 * frontend no conoce las membresías del usuario declarado: se declara el rol de desarrollo si la ruta
 * lo admite, o el primero que admita, y el servidor decide (403 si no lo tiene).
 */
function rolDeclarado(rolesPermitidos?: readonly string[]): string | null {
  const roles = leerOrganizacionActiva()?.roles ?? [];
  const permitidos = rolesPermitidos?.length ? rolesPermitidos : null;
  if (roles.length) {
    const candidatos = permitidos ?? [...PREFERENCIA_DE_ROL, ...roles.filter((rol) => !PREFERENCIA_DE_ROL.includes(rol))];
    return candidatos.find((candidato) => roles.includes(candidato)) ?? null;
  }
  if (modoAutenticacion() !== "headers") return null;
  const propio = identidadDeDesarrollo().rol;
  return !permitidos || permitidos.includes(propio) ? propio : permitidos[0];
}

/**
 * Para las rutas que resuelven al miembro con `get_context` (Biblioteca): organización, rol y, en
 * modo "headers", usuario. Con `rolesPermitidos` (los del `require_role` de la ruta) toma el primero
 * que el usuario tenga; sin ellos, el de mayor preferencia.
 *
 * Lanza `SinRolPermitido` si el usuario no tiene ninguno: la petición no llega a enviarse.
 */
export function cabecerasDeMiembro(rolesPermitidos?: readonly string[]): CabecerasIdentidad {
  const rol = rolDeclarado(rolesPermitidos);
  if (!rol) throw new SinRolPermitido(rolesPermitidos ?? []);
  const cabeceras: CabecerasIdentidad = { ...cabecerasDeTenant(), "X-Role": rol };
  if (modoAutenticacion() === "headers") cabeceras["X-User-ID"] = identidadDeDesarrollo().usuario;
  return cabeceras;
}

/**
 * Para las operaciones globales de plataforma, que deliberadamente no pertenecen a un tenant.
 * En producción la identidad procede del token; en desarrollo controlado se usan las cabeceras
 * que acepta el router de plataforma.
 */
export function cabecerasDePlataforma(): CabecerasIdentidad {
  if (modoAutenticacion() === "oidc") {
    const sesion = leerSesion();
    return sesion ? { Authorization: `Bearer ${sesion.token}` } : {};
  }
  return {
    "X-User-ID": process.env.NEXT_PUBLIC_USER_ID || "operador-plataforma-dev",
    "X-User-Email": process.env.NEXT_PUBLIC_USER_EMAIL || "operador@plataforma.test",
  };
}
