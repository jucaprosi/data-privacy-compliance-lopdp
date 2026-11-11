/**
 * Cliente y validación de sedes y clientes por encargo (ORG-18).
 *
 * Forma de las respuestas, tomada de `features/organizacion/services/sedes_engine.py`:
 * GET /organizacion/sedes → `[{id, nombre, direccion, ciudad, provincia, es_principal, contacto_spdp,
 * contacto_titulares, medidas, retirada_en}]`; GET /organizacion/clientes → `[{id, razon_social, ruc,
 * contrato_sha256, vigente_hasta, retirado_en}]`, o 409 `NO_ES_ENCARGADA` si la organización no trata datos
 * por encargo. Escriben `admin_organizacion`, `implementador` y `coordinador`; el `dpo` solo lee. La
 * organización y la identidad salen de la sesión: ningún cuerpo las lleva.
 */
import { requestJson } from "@/lib/roadmap/cliente";
import { ApiError } from "@/types/roadmap";
import type { OrganizacionRole } from "@/types/roadmap";

export interface Sede {
  id: string;
  nombre: string;
  direccion: string;
  ciudad: string;
  provincia: string;
  es_principal: boolean;
  contacto_spdp: string | null;
  contacto_titulares: string | null;
  medidas: string | null;
  retirada_en: string | null;
}
export interface Cliente {
  id: string;
  razon_social: string;
  ruc: string;
  contrato_sha256: string | null;
  vigente_hasta: string | null;
  retirado_en: string | null;
}

export interface BorradorSede {
  nombre: string;
  direccion: string;
  ciudad: string;
  provincia: string;
  esPrincipal: boolean;
  contactoSpdp: string;
  contactoTitulares: string;
  medidas: string;
}
export interface BorradorCliente {
  razonSocial: string;
  ruc: string;
  contratoSha256: string;
  vigenteHasta: string;
}

export const SEDE_VACIA: BorradorSede = {
  nombre: "", direccion: "", ciudad: "", provincia: "", esPrincipal: false, contactoSpdp: "", contactoTitulares: "", medidas: "",
};
export const CLIENTE_VACIO: BorradorCliente = { razonSocial: "", ruc: "", contratoSha256: "", vigenteHasta: "" };

/** Motivo visible que impide guardar, o null si la sede es válida. Misma regla que el servidor. */
export function validarSede(b: BorradorSede): string | null {
  if (!b.nombre.trim() || !b.direccion.trim() || !b.ciudad.trim() || !b.provincia.trim()) {
    return "Completa nombre, dirección, ciudad y provincia.";
  }
  return null;
}
export function validarCliente(b: BorradorCliente): string | null {
  if (!b.razonSocial.trim()) return "Escribe la razón social del cliente.";
  if (!/^[0-9]{13}$/.test(b.ruc.trim())) return "El RUC debe tener 13 dígitos.";
  if (b.contratoSha256.trim() && !/^[0-9a-fA-F]{64}$/.test(b.contratoSha256.trim())) {
    return "La huella del contrato debe tener 64 caracteres hexadecimales.";
  }
  return null;
}

const opcional = (valor: string) => (valor.trim() ? valor.trim() : null);

/** Cuerpos con los nombres de campo del servidor. Nunca llevan organización ni identidad. */
export const cuerpoSede = (b: BorradorSede) => ({
  nombre: b.nombre.trim(),
  direccion: b.direccion.trim(),
  ciudad: b.ciudad.trim(),
  provincia: b.provincia.trim(),
  es_principal: b.esPrincipal,
  contacto_spdp: opcional(b.contactoSpdp),
  contacto_titulares: opcional(b.contactoTitulares),
  medidas: opcional(b.medidas),
});
export const cuerpoCliente = (b: BorradorCliente) => ({
  razon_social: b.razonSocial.trim(),
  ruc: b.ruc.trim(),
  contrato_sha256: opcional(b.contratoSha256),
  vigente_hasta: opcional(b.vigenteHasta),
});

/** Puede escribir quien gestiona la organización; el dpo y el responsable de área solo leen (D-2). */
export const puedeEscribirSedes = (rol: OrganizacionRole | null): boolean =>
  rol === "admin_organizacion" || rol === "implementador" || rol === "coordinador";

export const esNoEsEncargada = (err: unknown): boolean => err instanceof ApiError && err.code === "NO_ES_ENCARGADA";

const conRol = (rol: OrganizacionRole) => ({ headers: { "X-Role": rol } });
const lista = <T>(crudo: unknown): T[] => (Array.isArray(crudo) ? (crudo as T[]) : []);

export const sedesApi = {
  async sedes(rol: OrganizacionRole): Promise<Sede[]> {
    return lista<Sede>(await requestJson<unknown>("/organizacion/sedes", { method: "GET", ...conRol(rol) }));
  },
  async crearSede(cuerpo: object, rol: OrganizacionRole): Promise<void> {
    await requestJson<unknown>("/organizacion/sedes", { method: "POST", body: JSON.stringify(cuerpo), ...conRol(rol) });
  },
  async retirarSede(id: string, rol: OrganizacionRole): Promise<void> {
    await requestJson<unknown>(`/organizacion/sedes/${id}/retirar`, { method: "POST", ...conRol(rol) });
  },
  async clientes(rol: OrganizacionRole): Promise<Cliente[]> {
    return lista<Cliente>(await requestJson<unknown>("/organizacion/clientes", { method: "GET", ...conRol(rol) }));
  },
  async crearCliente(cuerpo: object, rol: OrganizacionRole): Promise<void> {
    await requestJson<unknown>("/organizacion/clientes", { method: "POST", body: JSON.stringify(cuerpo), ...conRol(rol) });
  },
  async retirarCliente(id: string, rol: OrganizacionRole): Promise<void> {
    await requestJson<unknown>(`/organizacion/clientes/${id}/retirar`, { method: "POST", ...conRol(rol) });
  },
};
