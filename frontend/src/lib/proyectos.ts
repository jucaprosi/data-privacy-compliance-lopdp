/**
 * Biblioteca local de proyectos de assessment.
 *
 * Un proyecto es una instantánea del trabajo del auditor (ficha organizacional,
 * normativa, respuestas y avance) guardada con nombre. La biblioteca vive en el
 * almacenamiento del navegador: los datos del assessment no salen del equipo
 * (Doctrina 8, privacidad por diseño de la propia plataforma).
 *
 * Todo acceso al almacenamiento se protege: puede no existir (modo privado,
 * datos de sitio bloqueados) o contener datos corruptos, y en ninguno de esos
 * casos la aplicación debe romperse.
 */

import type {
  CompanyData,
  NormativaAuditoria,
  RespuestaItemStore,
} from "@/store/useAuditStore";
import type { EvidenciaDocumental } from "@/lib/evidencias/tipos";

const CLAVE_BIBLIOTECA = "jubys-proyectos-v1";
export const MAX_RECIENTES = 5;

export interface InstantaneaProyecto {
  companyData: CompanyData;
  normativaSeleccionada: NormativaAuditoria;
  isConfigured: boolean;
  respuestas: RespuestaItemStore[];
  preguntaActualIndex: number;
  timeboxRestante: number;
  /** Ausente en proyectos guardados antes del registro de evidencias. */
  evidencias?: EvidenciaDocumental[];
  correlativoEvidencias?: number;
}

export interface ProyectoGuardado {
  id: string;
  nombre: string;
  creadoEn: string;
  actualizadoEn: string;
  datos: InstantaneaProyecto;
}

export interface ResumenProyecto {
  id: string;
  nombre: string;
  actualizadoEn: string;
  razonSocial: string;
  respuestas: number;
}

interface Biblioteca {
  proyectos: ProyectoGuardado[];
  recientes: string[];
}

const BIBLIOTECA_VACIA: Biblioteca = { proyectos: [], recientes: [] };

function esInstantaneaValida(valor: unknown): valor is InstantaneaProyecto {
  if (!valor || typeof valor !== "object") return false;
  const v = valor as Record<string, unknown>;
  return (
    typeof v.companyData === "object" &&
    v.companyData !== null &&
    Array.isArray(v.respuestas) &&
    typeof v.isConfigured === "boolean" &&
    (v.evidencias === undefined || Array.isArray(v.evidencias))
  );
}

function esProyectoValido(valor: unknown): valor is ProyectoGuardado {
  if (!valor || typeof valor !== "object") return false;
  const v = valor as Record<string, unknown>;
  return (
    typeof v.id === "string" &&
    typeof v.nombre === "string" &&
    typeof v.actualizadoEn === "string" &&
    esInstantaneaValida(v.datos)
  );
}

function leerBiblioteca(): Biblioteca {
  try {
    const crudo = window.localStorage.getItem(CLAVE_BIBLIOTECA);
    if (!crudo) return { ...BIBLIOTECA_VACIA };
    const parsed = JSON.parse(crudo) as Partial<Biblioteca>;
    const proyectos = Array.isArray(parsed.proyectos)
      ? parsed.proyectos.filter(esProyectoValido)
      : [];
    const ids = new Set(proyectos.map((p) => p.id));
    const recientes = Array.isArray(parsed.recientes)
      ? parsed.recientes.filter((id): id is string => typeof id === "string" && ids.has(id))
      : [];
    return { proyectos, recientes };
  } catch {
    return { ...BIBLIOTECA_VACIA };
  }
}

function escribirBiblioteca(biblioteca: Biblioteca): boolean {
  try {
    window.localStorage.setItem(CLAVE_BIBLIOTECA, JSON.stringify(biblioteca));
    return true;
  } catch {
    return false;
  }
}

function conReciente(recientes: string[], id: string): string[] {
  return [id, ...recientes.filter((r) => r !== id)].slice(0, MAX_RECIENTES);
}

function generarId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `proy-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function resumir(p: ProyectoGuardado): ResumenProyecto {
  return {
    id: p.id,
    nombre: p.nombre,
    actualizadoEn: p.actualizadoEn,
    razonSocial: p.datos.companyData.razonSocial,
    respuestas: p.datos.respuestas.filter((r) => !r.esReferencia).length,
  };
}

/** Proyectos guardados, del más reciente al más antiguo. */
export function listarProyectos(): ResumenProyecto[] {
  return leerBiblioteca()
    .proyectos.slice()
    .sort((a, b) => b.actualizadoEn.localeCompare(a.actualizadoEn))
    .map(resumir);
}

/** Últimos proyectos abiertos o guardados, en orden de uso. */
export function listarRecientes(): ResumenProyecto[] {
  const { proyectos, recientes } = leerBiblioteca();
  return recientes
    .map((id) => proyectos.find((p) => p.id === id))
    .filter((p): p is ProyectoGuardado => Boolean(p))
    .map(resumir);
}

/**
 * Guarda la instantánea. Con `id` sobrescribe ese proyecto; sin él crea uno
 * nuevo. Devuelve el proyecto guardado, o null si el almacenamiento falló.
 */
export function guardarProyecto(
  datos: InstantaneaProyecto,
  nombre: string,
  id?: string
): ProyectoGuardado | null {
  const biblioteca = leerBiblioteca();
  const ahora = new Date().toISOString();
  const existente = id ? biblioteca.proyectos.find((p) => p.id === id) : undefined;

  const proyecto: ProyectoGuardado = {
    id: existente?.id ?? generarId(),
    nombre: nombre.trim() || existente?.nombre || "Proyecto sin nombre",
    creadoEn: existente?.creadoEn ?? ahora,
    actualizadoEn: ahora,
    datos,
  };

  const proyectos = existente
    ? biblioteca.proyectos.map((p) => (p.id === proyecto.id ? proyecto : p))
    : [...biblioteca.proyectos, proyecto];

  const ok = escribirBiblioteca({
    proyectos,
    recientes: conReciente(biblioteca.recientes, proyecto.id),
  });
  return ok ? proyecto : null;
}

/** Recupera un proyecto y lo registra como reciente. */
export function abrirProyecto(id: string): ProyectoGuardado | null {
  const biblioteca = leerBiblioteca();
  const proyecto = biblioteca.proyectos.find((p) => p.id === id);
  if (!proyecto) return null;
  escribirBiblioteca({
    ...biblioteca,
    recientes: conReciente(biblioteca.recientes, id),
  });
  return proyecto;
}
