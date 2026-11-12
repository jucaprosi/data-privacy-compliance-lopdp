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

export type CampoSede = "nombre" | "direccion" | "ciudad" | "provincia";
const NOMBRE_CAMPO_SEDE: Record<CampoSede, string> = {
  nombre: "nombre",
  direccion: "dirección",
  ciudad: "ciudad",
  provincia: "provincia",
};

/** Campos obligatorios de la sede que están vacíos, en el orden del formulario. */
export function faltantesSede(b: BorradorSede): CampoSede[] {
  return (["nombre", "direccion", "ciudad", "provincia"] as const).filter((c) => !b[c].trim());
}
/** «Falta: ciudad y provincia.»; null si no falta nada. Misma regla que el servidor. */
export function mensajeFaltantes(faltantes: CampoSede[]): string | null {
  if (faltantes.length === 0) return null;
  const nombres = faltantes.map((c) => NOMBRE_CAMPO_SEDE[c]);
  const lista = nombres.length === 1 ? nombres[0] : `${nombres.slice(0, -1).join(", ")} y ${nombres[nombres.length - 1]}`;
  return `Falta: ${lista}.`;
}
export function validarSede(b: BorradorSede): string | null {
  return mensajeFaltantes(faltantesSede(b));
}

export interface ErroresCliente {
  razonSocial?: string;
  ruc?: string;
  contrato?: string;
}
export function erroresCliente(b: BorradorCliente): ErroresCliente {
  const errores: ErroresCliente = {};
  if (!b.razonSocial.trim()) errores.razonSocial = "Escribe la razón social del cliente.";
  if (!/^[0-9]{13}$/.test(b.ruc.trim())) errores.ruc = "El RUC debe tener 13 dígitos.";
  if (b.contratoSha256.trim() && !/^[0-9a-fA-F]{64}$/.test(b.contratoSha256.trim())) {
    errores.contrato = "La huella debe tener 64 caracteres: números del 0 al 9 y letras de la a a la f.";
  }
  return errores;
}
export function validarCliente(b: BorradorCliente): string | null {
  const e = erroresCliente(b);
  return e.razonSocial ?? e.ruc ?? e.contrato ?? null;
}

/** «2026-10-28» → «28/10/2026» (es-EC). Sin zona horaria: la fecha llega como día calendario. */
export function formatearFecha(iso: string): string {
  const [anio, mes, dia] = iso.slice(0, 10).split("-");
  return anio && mes && dia ? `${dia}/${mes}/${anio}` : iso;
}
/** La vigencia venció si su día calendario es anterior a hoy. */
export function vigenciaVencida(iso: string, hoy: Date = new Date()): boolean {
  const hoyIso = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, "0")}-${String(hoy.getDate()).padStart(2, "0")}`;
  return iso.slice(0, 10) < hoyIso;
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
