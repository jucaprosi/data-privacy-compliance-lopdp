/**
 * Cabeceras de identidad: el único sitio donde el frontend decide qué identidad envía.
 *
 * Todos los clientes de la API las piden aquí (roadmap, preanálisis, bóveda de evidencias, ARCO,
 * terceros, mitigación...). Ninguno lleva ya un usuario, un tenant ni un token fijos en el código.
 *
 *  - "oidc": `Authorization: Bearer <token de Google>` + `X-Tenant-ID`. No se envía X-User-ID: el
 *    servidor lo ignoraría, y mandarlo sugeriría que cuenta.
 *  - "headers" (solo desarrollo): `X-Tenant-ID`, y para roadmap además `X-User-ID` y `X-Role`.
 */
import { modoAutenticacion, tenantConfigurado } from "./modo";
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
