/**
 * Cliente y validación del alta de la organización en siete pasos (ORG-16).
 *
 * Forma de las respuestas, tomada de `features/organizacion/services/alta_engine.py`:
 * GET /organizacion/alta → `{pasos: [{id, completo}], completo}`; GET /organizacion/alta/sugerencias →
 * `{tratamientos: [{indice, nombre, finalidad, base_legal}], terceros: [{indice, tipo, descripcion}]}`;
 * POST /organizacion/alta/paso/{id} → `{paso, completo}`. Escriben `admin_organizacion` e
 * `implementador`; el `dpo` y los demás roles solo leen el estado. La organización y la identidad salen
 * de la sesión: ningún cuerpo las lleva. El estado de cada paso es el del servidor; aquí no se guarda
 * ningún «configurado» local.
 */
import { requestJson } from "@/lib/roadmap/cliente";
import type { OrganizacionRole } from "@/types/roadmap";

export const PASOS_ALTA = ["perfil", "sedes", "areas", "tratamientos", "terceros", "personas", "resumen"] as const;
export type PasoAlta = (typeof PASOS_ALTA)[number];

export const TITULOS_PASO: Record<PasoAlta, string> = {
  perfil: "Perfil",
  sedes: "Sedes",
  areas: "Áreas",
  tratamientos: "Tratamientos sugeridos",
  terceros: "Terceros típicos",
  personas: "Personas clave",
  resumen: "Resumen",
};

/** Pasos que el servidor exige para completar el alta (R1). */
export const PASOS_OBLIGATORIOS: ReadonlySet<PasoAlta> = new Set<PasoAlta>(["perfil", "areas"]);

export interface EstadoPasoAlta {
  id: PasoAlta;
  completo: boolean;
}
export interface EstadoAlta {
  pasos: EstadoPasoAlta[];
  completo: boolean;
}
export interface SugerenciaTratamiento {
  indice: number;
  nombre: string;
  finalidad: string;
  base_legal: string;
}
export interface SugerenciaTercero {
  indice: number;
  tipo: string;
  descripcion: string;
}
export interface Sugerencias {
  tratamientos: SugerenciaTratamiento[];
  terceros: SugerenciaTercero[];
}

export const TAMANOS = ["micro", "pequena", "mediana", "corporativo"] as const;
export const NATURALEZAS = ["publica", "privada", "mixta"] as const;
export const ROLES_DATOS = ["responsable", "encargado", "ambos"] as const;
export const ROLES_PERSONA = ["coordinador", "responsable_area", "dpo"] as const;

export const ETIQUETA_TAMANO: Record<(typeof TAMANOS)[number], string> = {
  micro: "Micro",
  pequena: "Pequeña",
  mediana: "Mediana",
  corporativo: "Corporativa",
};
export const ETIQUETA_NATURALEZA: Record<(typeof NATURALEZAS)[number], string> = {
  publica: "Pública",
  privada: "Privada",
  mixta: "Mixta",
};
export const ETIQUETA_ROL_DATOS: Record<(typeof ROLES_DATOS)[number], string> = {
  responsable: "Responsable del tratamiento",
  encargado: "Encargada del tratamiento",
  ambos: "Ambos",
};
export const ETIQUETA_ROL_PERSONA: Record<(typeof ROLES_PERSONA)[number], string> = {
  coordinador: "Coordinador",
  responsable_area: "Responsable de área",
  dpo: "Delegado de protección de datos",
};

export interface BorradorPerfil {
  razonSocial: string;
  ruc: string;
  sector: string;
  tamano: string;
  naturaleza: string;
  rolDatos: string;
  actividadesRiesgo: string;
}
export interface BorradorSedes {
  domicilio: string;
  ciudad: string;
  provincia: string;
}
export interface BorradorArea {
  nombre: string;
  codigo: string;
}
export interface BorradorPersona {
  nombre: string;
  cargo: string;
  email: string;
  rol: string;
  areaId: string;
}

const CORREO = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export const esRucValido = (ruc: string) => /^[0-9]{13}$/.test(ruc.trim());
export const esCorreoValido = (correo: string) => CORREO.test(correo.trim());

/** Motivo visible que impide avanzar, o null si el paso es válido. Misma regla que el servidor. */
export function validarPerfil(b: BorradorPerfil): string | null {
  if (!b.razonSocial.trim()) return "Escribe la razón social de la organización.";
  if (!esRucValido(b.ruc)) return "El RUC debe tener 13 dígitos.";
  if (!b.sector.trim()) return "Escribe el sector de la organización.";
  if (!b.tamano) return "Elige el tamaño de la organización.";
  if (!b.naturaleza) return "Elige la naturaleza de la organización.";
  if (!b.rolDatos) return "Indica el rol de la organización frente a los datos.";
  return null;
}
export function validarSedes(b: BorradorSedes): string | null {
  if (!b.domicilio.trim() || !b.ciudad.trim() || !b.provincia.trim()) return "Completa domicilio, ciudad y provincia.";
  return null;
}
export function validarAreas(areas: BorradorArea[]): string | null {
  const con = areas.filter((a) => a.nombre.trim());
  return con.length === 0 ? "Agrega al menos un área." : null;
}
export function validarPersonas(personas: BorradorPersona[]): string | null {
  if (personas.length === 0) return "Agrega al menos una persona o salta este paso.";
  for (const p of personas) {
    if (!p.nombre.trim() || !p.cargo.trim()) return "Cada persona necesita nombre y cargo.";
    if (!esCorreoValido(p.email)) return "Revisa el correo de cada persona.";
    if (!p.rol) return "Elige el rol propuesto de cada persona.";
  }
  return null;
}

/** Cuerpos de cada paso, con los nombres de campo del servidor. Nunca llevan organización ni identificación. */
export const cuerposAlta = {
  perfil: (b: BorradorPerfil) => ({
    razon_social: b.razonSocial.trim(),
    ruc: b.ruc.trim(),
    sector: b.sector.trim(),
    tamano: b.tamano,
    naturaleza: b.naturaleza,
    rol_datos: b.rolDatos,
    actividades_riesgo: b.actividadesRiesgo.split(",").map((a) => a.trim()).filter(Boolean),
  }),
  sedes: (b: BorradorSedes) => ({ domicilio: b.domicilio.trim(), ciudad: b.ciudad.trim(), provincia: b.provincia.trim() }),
  areas: (areas: BorradorArea[]) => ({
    areas: areas
      .filter((a) => a.nombre.trim())
      .map((a) => ({ nombre: a.nombre.trim(), ...(a.codigo.trim() ? { codigo: a.codigo.trim() } : {}) })),
  }),
  tratamientos: (aceptados: number[]) => ({ aceptados: [...aceptados].sort((x, y) => x - y), ajustes: [] }),
  personas: (personas: BorradorPersona[]) => ({
    personas: personas.map((p) => ({
      nombre: p.nombre.trim(),
      cargo: p.cargo.trim(),
      email: p.email.trim(),
      rol: p.rol,
      ...(p.areaId ? { area_id: p.areaId } : {}),
    })),
  }),
  resumen: () => ({}),
};

/** Puede iniciar o continuar el alta quien escribe en el servidor (el dpo no, D-2). */
export const puedeEscribirAlta = (rol: OrganizacionRole | null): boolean =>
  rol === "admin_organizacion" || rol === "implementador";

function conRol(rol: OrganizacionRole): { headers: Record<string, string> } {
  return { headers: { "X-Role": rol } };
}

/** Toma de la respuesta solo lo que el contrato define; cualquier otra cosa cuenta como paso sin completar. */
export function normalizarEstado(crudo: unknown): EstadoAlta {
  const objeto = crudo && typeof crudo === "object" && !Array.isArray(crudo) ? (crudo as Record<string, unknown>) : {};
  const lista = Array.isArray(objeto.pasos) ? (objeto.pasos as unknown[]) : [];
  const completos = new Set(
    lista
      .filter((p): p is { id: string; completo: boolean } => !!p && typeof p === "object" && (p as { completo?: unknown }).completo === true)
      .map((p) => p.id),
  );
  const pasos = PASOS_ALTA.map((id) => ({ id, completo: completos.has(id) }));
  return { pasos, completo: objeto.completo === true };
}

export const altaApi = {
  async estado(rol: OrganizacionRole): Promise<EstadoAlta> {
    return normalizarEstado(await requestJson<unknown>("/organizacion/alta", { method: "GET", ...conRol(rol) }));
  },
  async sugerencias(rol: OrganizacionRole): Promise<Sugerencias> {
    const crudo = await requestJson<Partial<Sugerencias>>("/organizacion/alta/sugerencias", { method: "GET", ...conRol(rol) });
    return {
      tratamientos: Array.isArray(crudo.tratamientos) ? crudo.tratamientos : [],
      terceros: Array.isArray(crudo.terceros) ? crudo.terceros : [],
    };
  },
  async guardarPaso(paso: PasoAlta, cuerpo: object, rol: OrganizacionRole): Promise<void> {
    await requestJson<unknown>(`/organizacion/alta/paso/${paso}`, {
      method: "POST",
      body: JSON.stringify(cuerpo),
      ...conRol(rol),
    });
  },
};
