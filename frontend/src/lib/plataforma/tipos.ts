export type TamanoOrganizacion = "micro" | "pequena" | "mediana" | "corporativo";

export interface OrganizacionCrear {
  nombre_comercial: string;
  razon_social: string;
  ruc_identificacion: string;
  tamano: TamanoOrganizacion;
  sector: string;
  email_admin_inicial: string;
}

export interface OrganizacionResumen {
  id: string;
  nombre_comercial: string;
  razon_social: string;
  ruc_identificacion: string;
  activo: boolean | null;
  created_at: string | null;
  email_admin_inicial: string | null;
  invitacion_estado: string | null;
}

export interface AltaOrganizacion {
  tenant_id: string;
  invitacion_id: string;
  codigo_invitacion: string;
  expira_en: string;
  email_invitado: string;
}

export interface AceptacionInvitacion {
  tenant_id: string;
  user_id: string;
  email: string;
  rol_asignado: string;
  mensaje: string;
}

export interface ErrorApiPlataforma {
  detail?: string;
  code?: string;
}
