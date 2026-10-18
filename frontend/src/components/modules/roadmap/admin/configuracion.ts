/**
 * Cliente de la configuración de la organización (tamaño y sector).
 *
 * Forma de la respuesta, comprobada contra el servidor (`features/organizacion/services/
 * configuracion_engine.py`): GET y PATCH /organizacion/configuracion devuelven
 * `{id, nombre_comercial, razon_social, ruc_identificacion, sector, tamano, activo}`. Aquí solo se
 * leen `tamano` y `sector`; el resto se ignora. GET lo puede pedir cualquier rol activo; PATCH solo
 * `admin_organizacion`.
 *
 * Las claves y etiquetas de tamaño no se definen aquí: vienen de `lib/tamanoOrganizacion.ts`.
 */
import { requestJson } from "../../../../lib/roadmap/cliente";
import { TAMANOS_ORGANIZACION } from "../../../../lib/tamanoOrganizacion";
import type { OrganizacionRole } from "../../../../types/roadmap";

/** Opciones del selector de tamaño del panel: clave del servidor y nombre corto. */
export const TAMANOS: ReadonlyArray<{ clave: string; etiqueta: string }> = TAMANOS_ORGANIZACION.map((t) => ({
  clave: t.clave,
  etiqueta: t.etiqueta,
}));

export interface ConfiguracionOrganizacion {
  tamano: string | null;
  sector: string | null;
}

export interface ConfiguracionCambios {
  tamano?: string | null;
  sector?: string | null;
}

/** El rol con el que se actúa. Sin él se usa el rol activo de la sesión. */
function conRol(rol?: OrganizacionRole): { headers?: Record<string, string> } {
  return rol ? { headers: { "X-Role": rol } } : {};
}

export const configuracionApi = {
  obtener(rol?: OrganizacionRole): Promise<ConfiguracionOrganizacion> {
    return requestJson<ConfiguracionOrganizacion>("/organizacion/configuracion", { method: "GET", ...conRol(rol) });
  },
  guardar(cambios: ConfiguracionCambios, rol?: OrganizacionRole): Promise<ConfiguracionOrganizacion> {
    return requestJson<ConfiguracionOrganizacion>("/organizacion/configuracion", {
      method: "PATCH",
      body: JSON.stringify(cambios),
      ...conRol(rol),
    });
  },
};
