/**
 * Cliente y validación del inventario de activos, soportes y personas (ORG-17).
 *
 * Forma de las respuestas, tomada de `features/organizacion/services/inventario_engine.py`:
 * GET /organizacion/inventario/activos → `[{id, tipo, nombre, descripcion, ubicacion, area_id, responsable_id,
 * archivado, tratamiento_ids}]`; GET .../personas → `[{id, nombre, cargo, area_id, email, tiene_cedula,
 * archivada}]` (la cédula nunca se devuelve); GET .../tratamientos → `[{id, codigo, nombre}]`. Escriben
 * `admin_organizacion`, `implementador` y `coordinador`; el `dpo` solo lee. La organización y la identidad
 * salen de la sesión: ningún cuerpo las lleva.
 */
import { requestJson } from "@/lib/roadmap/cliente";
import type { OrganizacionRole } from "@/types/roadmap";

export const TIPOS_ACTIVO = ["sistema", "soporte_fisico", "soporte_digital"] as const;
export type TipoActivo = (typeof TIPOS_ACTIVO)[number];

export const ETIQUETA_TIPO: Record<TipoActivo, string> = {
  sistema: "Sistema",
  soporte_fisico: "Soporte físico",
  soporte_digital: "Soporte digital",
};

export interface Activo {
  id: string;
  tipo: TipoActivo;
  nombre: string;
  descripcion: string | null;
  ubicacion: string | null;
  area_id: string | null;
  responsable_id: string | null;
  archivado: boolean;
  tratamiento_ids: string[];
}
export interface PersonaInventario {
  id: string;
  nombre: string;
  cargo: string;
  area_id: string | null;
  email: string;
  tiene_cedula: boolean;
  archivada: boolean;
}
export interface TratamientoVinculable {
  id: string;
  codigo: string;
  nombre: string;
}

export interface BorradorActivo {
  nombre: string;
  descripcion: string;
  ubicacion: string;
  areaId: string;
  responsableId: string;
}
export interface BorradorPersonaInventario {
  nombre: string;
  cargo: string;
  email: string;
  areaId: string;
  cedula: string;
}

const CORREO = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export const esCorreoValido = (correo: string) => CORREO.test(correo.trim());

/** Motivo visible que impide guardar, o null si el activo es válido. */
export function validarActivo(b: BorradorActivo): string | null {
  return b.nombre.trim() ? null : "Escribe el nombre.";
}
/** Motivo visible que impide guardar, o null si la persona es válida. La cédula es opcional. */
export function validarPersona(b: BorradorPersonaInventario): string | null {
  if (!b.nombre.trim() || !b.cargo.trim()) return "Cada persona necesita nombre y cargo.";
  if (!esCorreoValido(b.email)) return "Revisa el correo.";
  if (b.cedula.trim() && !/^[0-9]{10}$/.test(b.cedula.trim())) return "La cédula debe tener 10 dígitos.";
  return null;
}

/** Cuerpos con los nombres de campo del servidor. Nunca llevan organización ni identidad. */
export const cuerpoActivo = (tipo: TipoActivo, b: BorradorActivo) => ({
  tipo,
  nombre: b.nombre.trim(),
  ...(b.descripcion.trim() ? { descripcion: b.descripcion.trim() } : {}),
  ...(b.ubicacion.trim() ? { ubicacion: b.ubicacion.trim() } : {}),
  ...(b.areaId ? { area_id: b.areaId } : {}),
  ...(b.responsableId ? { responsable_id: b.responsableId } : {}),
});
export const cuerpoPersona = (b: BorradorPersonaInventario) => ({
  nombre: b.nombre.trim(),
  cargo: b.cargo.trim(),
  email: b.email.trim(),
  ...(b.areaId ? { area_id: b.areaId } : {}),
  ...(b.cedula.trim() ? { cedula: b.cedula.trim() } : {}),
});

/** Puede escribir quien gestiona la organización; el dpo y el responsable de área solo leen (D-2). */
export const puedeEscribirInventario = (rol: OrganizacionRole | null): boolean =>
  rol === "admin_organizacion" || rol === "implementador" || rol === "coordinador";

const BASE = "/organizacion/inventario";
const conRol = (rol: OrganizacionRole) => ({ headers: { "X-Role": rol } });
const lista = <T>(crudo: unknown): T[] => (Array.isArray(crudo) ? (crudo as T[]) : []);

export const inventarioApi = {
  async activos(rol: OrganizacionRole): Promise<Activo[]> {
    return lista<Activo>(await requestJson<unknown>(`${BASE}/activos`, { method: "GET", ...conRol(rol) }));
  },
  async crearActivo(cuerpo: object, rol: OrganizacionRole): Promise<void> {
    await requestJson<unknown>(`${BASE}/activos`, { method: "POST", body: JSON.stringify(cuerpo), ...conRol(rol) });
  },
  async editarActivo(id: string, cuerpo: object, rol: OrganizacionRole): Promise<void> {
    await requestJson<unknown>(`${BASE}/activos/${id}`, { method: "PATCH", body: JSON.stringify(cuerpo), ...conRol(rol) });
  },
  async vincularTratamientos(id: string, tratamientoIds: string[], rol: OrganizacionRole): Promise<void> {
    await requestJson<unknown>(`${BASE}/activos/${id}/tratamientos`, {
      method: "PUT",
      body: JSON.stringify({ tratamiento_ids: tratamientoIds }),
      ...conRol(rol),
    });
  },
  async tratamientos(rol: OrganizacionRole): Promise<TratamientoVinculable[]> {
    return lista<TratamientoVinculable>(await requestJson<unknown>(`${BASE}/tratamientos`, { method: "GET", ...conRol(rol) }));
  },
  async personas(rol: OrganizacionRole): Promise<PersonaInventario[]> {
    return lista<PersonaInventario>(await requestJson<unknown>(`${BASE}/personas`, { method: "GET", ...conRol(rol) }));
  },
  async crearPersona(cuerpo: object, rol: OrganizacionRole): Promise<void> {
    await requestJson<unknown>(`${BASE}/personas`, { method: "POST", body: JSON.stringify(cuerpo), ...conRol(rol) });
  },
  async editarPersona(id: string, cuerpo: object, rol: OrganizacionRole): Promise<void> {
    await requestJson<unknown>(`${BASE}/personas/${id}`, { method: "PATCH", body: JSON.stringify(cuerpo), ...conRol(rol) });
  },
};
