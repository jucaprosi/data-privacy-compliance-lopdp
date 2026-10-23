/**
 * Cliente de las designaciones formales de la organización (DPD y Coordinador).
 *
 * Implementa la interfaz con los 7 endpoints de ORG-06 (/api/v1/organizacion/designaciones):
 * - POST /: Crear designación formal (solo admin_organizacion).
 * - GET /: Listar designaciones formales (admin_organizacion, coordinador, dpo, implementador).
 * - GET /estado: Informe de estado de solo lectura (admin_organizacion, coordinador, dpo, implementador).
 * - GET /{id}: Ver detalle de una designación formal.
 * - POST /{id}/declarar: Registrar declaración previa de conflictos (SOLO la propia persona designada).
 * - POST /{id}/inscribir: Registrar constancia de inscripción ante SPDP (solo admin_organizacion).
 * - POST /{id}/revocar: Revocar formalmente la designación (solo admin_organizacion).
 *
 * Principios:
 * - El cliente nunca concede permisos que el backend rechazaría.
 * - Sin tokens estigmérgicos en código ni en interfaz pública.
 */
import { requestJson } from "../../../../lib/roadmap/cliente";
import type { OrganizacionRole } from "../../../../types/roadmap";

export type TipoDesignacion = "dpd" | "coordinador";
export type VinculoDesignacion = "relacion_dependencia" | "prestacion_servicios";

export interface DesignacionFormal {
  id: string;
  tenant_id: string;
  tipo: TipoDesignacion;
  user_id: string;
  representante_nombre: string;
  representante_identificacion: string;
  representante_cargo: string;
  fecha_designacion: string;
  doc_referencia: string;
  valid_from?: string | null;
  valid_to?: string | null;
  vinculo?: VinculoDesignacion | null;
  aceptacion_at?: string | null;
  declaracion_at?: string | null;
  declaracion_texto?: string | null;
  declaracion_tiene_conflicto?: boolean;
  declaracion_es_socio_accionista?: boolean;
  declaracion_es_pariente_admin?: boolean;
  inscripcion_spdp_fecha?: string | null;
  inscripcion_spdp_ref?: string | null;
  revocada_at?: string | null;
  revocada_motivo?: string | null;
  revocada_por_user_id?: string | null;
  created_at?: string;
  updated_at?: string;
  usuario_nombre?: string | null;
  usuario_email?: string | null;
}

export interface CargoIncompatibleResumen {
  id: string;
  nombre: string;
  tipo_cargo: string;
  area_id: string;
  area_nombre?: string;
}

export interface EstadoDesignacionDpd {
  designado: boolean;
  designacion: DesignacionFormal | null;
  declaracion_completada: boolean;
  inscrito_spdp: boolean;
  conflicto_sobrevenido: boolean;
  cargos_incompatibles: CargoIncompatibleResumen[];
  alertas: string[];
}

export interface EstadoDesignacionCoordinador {
  designado: boolean;
  designacion: DesignacionFormal | null;
  tiene_mandato_escrito: boolean;
  alertas: string[];
}

export interface InformeEstadoDesignaciones {
  tenant_id: string;
  dpd: EstadoDesignacionDpd;
  coordinador: EstadoDesignacionCoordinador;
}

export interface DesignacionCreatePayload {
  tipo: TipoDesignacion;
  user_id: string;
  representante_nombre: string;
  representante_identificacion: string;
  representante_cargo: string;
  fecha_designacion: string;
  doc_referencia: string;
  valid_to?: string | null;
  vinculo?: VinculoDesignacion | null;
}

export interface InscripcionSpdpPayload {
  inscripcion_spdp_fecha: string;
  inscripcion_spdp_ref: string;
}

export interface DeclaracionConflictosPayload {
  declaracion_texto: string;
  declaracion_tiene_conflicto?: boolean;
  declaracion_es_socio_accionista?: boolean;
  declaracion_es_pariente_admin?: boolean;
}

export interface RevocacionPayload {
  motivo: string;
}

export const ETIQUETAS_TIPO_DESIGNACION: Record<TipoDesignacion, string> = {
  dpd: "Delegado de Protección de Datos (DPD)",
  coordinador: "Coordinador de Protección de Datos",
};

export const ETIQUETAS_VINCULO: Record<VinculoDesignacion, string> = {
  relacion_dependencia: "Relación de dependencia",
  prestacion_servicios: "Prestación de servicios",
};

/** El rol con el que se actúa en las cabeceras HTTP. */
function conRol(rol?: OrganizacionRole): { headers?: Record<string, string> } {
  return rol ? { headers: { "X-Role": rol } } : {};
}

export const designacionesApi = {
  /**
   * Obtiene el informe de estado de solo lectura (DPD y Coordinador).
   */
  async obtenerEstado(rol?: OrganizacionRole): Promise<InformeEstadoDesignaciones> {
    return requestJson<InformeEstadoDesignaciones>("/organizacion/designaciones/estado", {
      method: "GET",
      ...conRol(rol),
    });
  },

  /**
   * Lista todas las designaciones formales registradas.
   */
  async listar(tipo?: TipoDesignacion, rol?: OrganizacionRole): Promise<DesignacionFormal[]> {
    const qs = tipo ? `?tipo=${encodeURIComponent(tipo)}` : "";
    return requestJson<DesignacionFormal[]>(`/organizacion/designaciones${qs}`, {
      method: "GET",
      ...conRol(rol),
    });
  },

  /**
   * Obtiene el detalle de una designación formal.
   */
  async obtener(id: string, rol?: OrganizacionRole): Promise<DesignacionFormal> {
    return requestJson<DesignacionFormal>(`/organizacion/designaciones/${encodeURIComponent(id)}`, {
      method: "GET",
      ...conRol(rol),
    });
  },

  /**
   * Crea una designación formal (DPD o Coordinador). Requiere admin_organizacion.
   */
  async crear(payload: DesignacionCreatePayload, rol?: OrganizacionRole): Promise<DesignacionFormal> {
    return requestJson<DesignacionFormal>("/organizacion/designaciones", {
      method: "POST",
      body: JSON.stringify(payload),
      ...conRol(rol),
    });
  },

  /**
   * Registra la declaración previa de conflictos (solo la persona designada).
   */
  async registrarDeclaracion(
    designacionId: string,
    payload: DeclaracionConflictosPayload,
    rol?: OrganizacionRole
  ): Promise<DesignacionFormal> {
    return requestJson<DesignacionFormal>(
      `/organizacion/designaciones/${encodeURIComponent(designacionId)}/declarar`,
      {
        method: "POST",
        body: JSON.stringify(payload),
        ...conRol(rol),
      }
    );
  },

  /**
   * Registra la constancia de inscripción ante la SPDP. Requiere admin_organizacion.
   */
  async registrarInscripcionSpdp(
    designacionId: string,
    payload: InscripcionSpdpPayload,
    rol?: OrganizacionRole
  ): Promise<DesignacionFormal> {
    return requestJson<DesignacionFormal>(
      `/organizacion/designaciones/${encodeURIComponent(designacionId)}/inscribir`,
      {
        method: "POST",
        body: JSON.stringify(payload),
        ...conRol(rol),
      }
    );
  },

  /**
   * Revoca formalmente la designación. Requiere admin_organizacion.
   */
  async revocar(
    designacionId: string,
    payload: RevocacionPayload,
    rol?: OrganizacionRole
  ): Promise<DesignacionFormal> {
    return requestJson<DesignacionFormal>(
      `/organizacion/designaciones/${encodeURIComponent(designacionId)}/revocar`,
      {
        method: "POST",
        body: JSON.stringify(payload),
        ...conRol(rol),
      }
    );
  },
};
