/**
 * Tipos para RAT-08: Área responsable vinculada a la estructura de la organización.
 */
import { ActividadRAT } from "./index";

export interface AreaOrganizacion {
  id: string;
  tenant_id?: string;
  nombre: string;
  codigo?: string | null;
  parent_area_id?: string | null;
  deleted_at?: string | null;
}

export interface ActividadRATConArea extends ActividadRAT {
  area_id?: string | null;
}
