/**
 * Cliente de la estructura orgánica de la organización (unidades, cargos, titulares y vacantes).
 *
 * Implementa la interfaz con los 7 endpoints de ORG-07 (/api/v1/organizacion/estructura):
 * - GET /arbol: Árbol completo de unidades, cargos, titulares y vacantes.
 * - GET /cobertura: Informe de cobertura (unidades sin jefatura, jefaturas vacantes, responsables por designar).
 * - POST /areas: Crear unidad orgánica.
 * - PATCH /areas/{area_id}: Editar unidad orgánica.
 * - POST /cargos: Crear cargo orgánico.
 * - PATCH /cargos/{cargo_id}: Editar cargo orgánico.
 * - POST /cargos/{cargo_id}/titular: Asignar o remover titular.
 *
 * Principios:
 * - El cliente nunca concede permisos que el backend rechazaría.
 * - Sin tokens estigmérgicos en código ni en interfaz pública.
 */
import { requestJson } from "../../../../lib/roadmap/cliente";
import type { OrganizacionRole } from "../../../../types/roadmap";

export type NivelAreaEstructura = "alta_direccion" | "direccion" | "jefatura" | "unidad";

export type TipoCargoEstructura =
  | "oficial_cumplimiento"
  | "oficial_seguridad_informacion"
  | "apoderado_especial_extranjero"
  | "miembro_administracion_o_control"
  | "implementador_proteccion_datos"
  | "nivel_superior_sector_publico"
  | "delegado_proteccion_datos"
  | "otro";

export interface CargoOrganico {
  id: string;
  tenant_id: string;
  area_id: string;
  nombre: string;
  tipo_cargo: TipoCargoEstructura;
  es_jefatura: boolean;
  reporta_a_cargo_id: string | null;
  titular_user_id: string | null;
  valid_to: string | null;
  created_at?: string;
  updated_at?: string;
  titular_nombre?: string | null;
  titular_email?: string | null;
}

export interface AreaEstructuraNodo {
  id: string;
  tenant_id: string;
  nombre: string;
  codigo: string | null;
  nivel: NivelAreaEstructura;
  parent_area_id: string | null;
  responsable_user_id: string | null;
  deleted_at: string | null;
  created_at?: string;
  updated_at?: string;
  cargos: CargoOrganico[];
  subareas: AreaEstructuraNodo[];
}

export interface ArbolEstructuraResponse {
  tenant_id: string;
  arbol: AreaEstructuraNodo[];
  total_areas: number;
  total_cargos: number;
}

export interface UnidadSinJefatura {
  area_id: string;
  nombre_area: string;
  nivel: NivelAreaEstructura;
}

export interface JefaturaVacante {
  area_id: string;
  nombre_area: string;
  cargo_id: string;
  nombre_cargo: string;
}

export interface ResponsablePorDesignar {
  area_id: string;
  nombre_area: string;
  cargo_id: string;
  nombre_cargo: string;
  candidato_user_id: string;
  candidato_nombre: string | null;
  candidato_email: string | null;
  motivo: string;
}

export interface InformeCoberturaResponse {
  tenant_id: string;
  total_unidades: number;
  unidades_sin_jefatura: UnidadSinJefatura[];
  jefaturas_vacantes: JefaturaVacante[];
  responsables_por_designar: ResponsablePorDesignar[];
}

export interface AreaEstructuraCreatePayload {
  nombre: string;
  codigo?: string | null;
  nivel?: NivelAreaEstructura;
  parent_area_id?: string | null;
}

export interface AreaEstructuraUpdatePayload {
  nombre?: string;
  codigo?: string | null;
  nivel?: NivelAreaEstructura;
  parent_area_id?: string | null;
  responsable_user_id?: string | null;
}

export interface CargoCreatePayload {
  area_id: string;
  nombre: string;
  tipo_cargo?: TipoCargoEstructura;
  es_jefatura?: boolean;
  reporta_a_cargo_id?: string | null;
  titular_user_id?: string | null;
  valid_to?: string | null;
}

export interface CargoUpdatePayload {
  area_id?: string;
  nombre?: string;
  tipo_cargo?: TipoCargoEstructura;
  es_jefatura?: boolean;
  reporta_a_cargo_id?: string | null;
  titular_user_id?: string | null;
  valid_to?: string | null;
}

export interface CargoTitularSetPayload {
  titular_user_id: string | null;
}

export const ETIQUETAS_NIVEL: Record<NivelAreaEstructura, string> = {
  alta_direccion: "Alta Dirección",
  direccion: "Dirección",
  jefatura: "Jefatura",
  unidad: "Unidad",
};

export const ETIQUETAS_TIPO_CARGO: Record<TipoCargoEstructura, string> = {
  oficial_cumplimiento: "Oficial de Cumplimiento",
  oficial_seguridad_informacion: "Oficial de Seguridad de la Información (CISO)",
  apoderado_especial_extranjero: "Apoderado Especial Extranjero",
  miembro_administracion_o_control: "Miembro de Administración o Control",
  implementador_proteccion_datos: "Implementador de Protección de Datos",
  nivel_superior_sector_publico: "Nivel Superior Sector Público",
  delegado_proteccion_datos: "Delegado de Protección de Datos (DPD / DPO)",
  otro: "Operativo / General",
};

/** El rol con el que se actúa en las cabeceras HTTP. */
function conRol(rol?: OrganizacionRole): { headers?: Record<string, string> } {
  return rol ? { headers: { "X-Role": rol } } : {};
}

export const estructuraApi = {
  obtenerArbol(rol?: OrganizacionRole): Promise<ArbolEstructuraResponse> {
    return requestJson<ArbolEstructuraResponse>("/organizacion/estructura/arbol", {
      method: "GET",
      ...conRol(rol),
    });
  },

  obtenerCobertura(rol?: OrganizacionRole): Promise<InformeCoberturaResponse> {
    return requestJson<InformeCoberturaResponse>("/organizacion/estructura/cobertura", {
      method: "GET",
      ...conRol(rol),
    });
  },

  crearArea(payload: AreaEstructuraCreatePayload, rol?: OrganizacionRole): Promise<Record<string, unknown>> {
    return requestJson<Record<string, unknown>>("/organizacion/estructura/areas", {
      method: "POST",
      body: JSON.stringify(payload),
      ...conRol(rol),
    });
  },

  editarArea(
    areaId: string,
    payload: AreaEstructuraUpdatePayload,
    rol?: OrganizacionRole
  ): Promise<Record<string, unknown>> {
    return requestJson<Record<string, unknown>>(`/organizacion/estructura/areas/${encodeURIComponent(areaId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
      ...conRol(rol),
    });
  },

  crearCargo(payload: CargoCreatePayload, rol?: OrganizacionRole): Promise<CargoOrganico> {
    return requestJson<CargoOrganico>("/organizacion/estructura/cargos", {
      method: "POST",
      body: JSON.stringify(payload),
      ...conRol(rol),
    });
  },

  editarCargo(
    cargoId: string,
    payload: CargoUpdatePayload,
    rol?: OrganizacionRole
  ): Promise<CargoOrganico> {
    return requestJson<CargoOrganico>(`/organizacion/estructura/cargos/${encodeURIComponent(cargoId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
      ...conRol(rol),
    });
  },

  asignarTitular(
    cargoId: string,
    titularUserId: string | null,
    rol?: OrganizacionRole
  ): Promise<CargoOrganico> {
    const payload: CargoTitularSetPayload = { titular_user_id: titularUserId };
    return requestJson<CargoOrganico>(`/organizacion/estructura/cargos/${encodeURIComponent(cargoId)}/titular`, {
      method: "POST",
      body: JSON.stringify(payload),
      ...conRol(rol),
    });
  },
};
