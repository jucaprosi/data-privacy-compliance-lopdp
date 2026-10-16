/**
 * Adaptador PROVISIONAL de la configuración de la organización.
 *
 * El backend de GET y PATCH /organizacion/configuracion lo construye la tarea RM-15 y aún no
 * existe. Este adaptador sigue el contrato de su especificación (tamaño y sector) y vive aquí
 * porque el cliente de FE-01 no lo expone. NO está verificado contra el backend real: cuando
 * RM-15 se integre, hay que confirmar la forma de la respuesta y moverlo al cliente.
 */
import { requestJson } from "../../../../lib/roadmap/cliente";

/** Claves de tamaño de domain/tamanos.py del backend, con la etiqueta que ve la persona usuaria. */
export const TAMANOS: ReadonlyArray<{ clave: string; etiqueta: string }> = [
  { clave: "micro", etiqueta: "Microempresa" },
  { clave: "pequena", etiqueta: "Pequeña empresa" },
  { clave: "mediana", etiqueta: "Mediana empresa" },
  { clave: "corporativo", etiqueta: "Corporativo" },
];

export interface ConfiguracionOrganizacion {
  tamano: string | null;
  sector: string | null;
}

export interface ConfiguracionCambios {
  tamano?: string | null;
  sector?: string | null;
}

export const configuracionApi = {
  obtener(): Promise<ConfiguracionOrganizacion> {
    return requestJson<ConfiguracionOrganizacion>("/organizacion/configuracion", { method: "GET" });
  },
  guardar(cambios: ConfiguracionCambios): Promise<ConfiguracionOrganizacion> {
    return requestJson<ConfiguracionOrganizacion>("/organizacion/configuracion", {
      method: "PATCH",
      body: JSON.stringify(cambios),
    });
  },
};
