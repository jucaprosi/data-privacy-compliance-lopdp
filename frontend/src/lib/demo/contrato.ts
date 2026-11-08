/**
 * Contrato congelado de la demo comercial (DEMO-04). ¤demo ¤interfaz
 *
 * Rutas, cuerpos y códigos de FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md §1.7; textos literales de
 * UX_DEMO_EVYDENTIA.md (validados por el propietario el 2026-11-07). Este archivo no habla con el
 * servidor: solo fija tipos y textos.
 */

export const RUTAS_DEMO = {
  entorno: "/api/v1/entorno",
  estado: "/api/v1/demo/estado",
  entrar: "/api/v1/demo/entrar",
  persona: "/api/v1/demo/persona",
  terminar: "/api/v1/demo/terminar",
} as const;

export type RolDemo =
  | "admin_organizacion"
  | "dpo"
  | "coordinador"
  | "implementador"
  | "responsable_area"
  | "auditor";

/** Orden fijo del ciclo que se enseña (UX_DEMO_EVYDENTIA §2). El primero es la persona de arranque. */
export const ORDEN_DE_ROLES: readonly RolDemo[] = [
  "admin_organizacion",
  "dpo",
  "coordinador",
  "implementador",
  "responsable_area",
  "auditor",
];

/** Línea descriptiva por rol: texto literal validado. */
export const LINEA_DE_ROL: Record<RolDemo, string> = {
  admin_organizacion: "Configura la organización y sus unidades, designa al DPO y al coordinador y asigna los dominios.",
  dpo: "Supervisa con independencia: reúne el soporte del diagnóstico, lo sella y valida la evidencia.",
  coordinador: "Reparte las tareas a las áreas y hace la primera validación de la evidencia.",
  implementador: "Acompaña el RAT, la Biblioteca y el plan de acción.",
  responsable_area: "Responde los dominios de su unidad, ejecuta sus tareas y carga la evidencia.",
  auditor: "Audita por dominio, levanta actas por área y verifica las acciones correctivas.",
};

/** Rol corto para el avatar en pantallas medianas. */
export const ROL_CORTO: Record<RolDemo, string> = {
  admin_organizacion: "Admin",
  dpo: "DPO",
  coordinador: "Coord.",
  implementador: "Impl.",
  responsable_area: "Resp.",
  auditor: "Auditor",
};

/** Recorrido sugerido de los cuatro ojos; al pulsarlo se cambia a su primer rol. */
export const RECORRIDO_SUGERIDO: readonly RolDemo[] = ["responsable_area", "coordinador", "dpo", "auditor"];

export interface PersonaDemo {
  usuario_id: string;
  nombre: string;
  rol: RolDemo;
  rol_etiqueta: string;
  unidad?: string | null;
}

export interface EstadoDemo {
  demo: boolean;
  organizacion: { tenant_id: string; nombre: string };
  persona_activa: PersonaDemo;
  personas: PersonaDemo[];
  vence_en?: string | null;
}

export type CodigoErrorDemo =
  | "DEMO_NO_AUTORIZADO"
  | "DEMO_OCUPADA"
  | "DEMO_VENCIDA"
  | "DEMO_PERSONA_AJENA"
  | "DEMO_NO_DISPONIBLE";

/** Textos literales del §1.7. */
export const TEXTO_DE_ERROR: Record<CodigoErrorDemo, string> = {
  DEMO_NO_AUTORIZADO: "No autorizado para la demo",
  DEMO_OCUPADA: "Demo ocupada, intenta en unos minutos",
  DEMO_VENCIDA: "Tu demostración terminó",
  DEMO_PERSONA_AJENA: "Esa persona no pertenece a tu demostración",
  DEMO_NO_DISPONIBLE: "No pudimos preparar la demo; intenta de nuevo",
};

export const TEXTOS_DEMO = {
  terminada: "La demo se cerró y sus datos se eliminan esta noche",
  vencidaDetalle:
    "Se cerró por inactividad o porque abriste una nueva (cada vendedor tiene una sola demo activa).",
  errorCambio: "No se pudo cambiar de persona. Intenta de nuevo.",
  tardando: "Está tardando un poco más de lo habitual",
  sigueFallando: "Si el problema sigue, avisa al equipo de EVYDENTIA",
  bienvenida: "Estás viendo la plataforma como Administrador de la organización. Cambia de persona en “Ver como”.",
  confirmarTitulo: "¿Terminar la demostración?",
  confirmarCuerpo: "La demostración se cierra ahora y sus datos se eliminan esta noche. No podrás volver a abrirla.",
} as const;

/** Pasos cualitativos de la entrada (UX_DEMO_EVYDENTIA §5), en el orden real de la copia. */
export const PASOS_DE_ENTRADA: readonly string[] = [
  "Creando la Cooperativa Demo y sus dos unidades",
  "Preparando a las seis personas",
  "Copiando el diagnóstico y la hoja de ruta",
  "Cargando documentos y evidencias",
  "Abriendo la plataforma como Administrador",
];

export const TIEMPOS_DE_ENTRADA = { pasoMs: 3_000, tardandoMs: 20_000, limiteMs: 60_000 } as const;

export function etiquetaDePersona(p: PersonaDemo): string {
  return p.unidad ? `${p.rol_etiqueta} · ${p.unidad}` : p.rol_etiqueta;
}

export function ordenarPersonas(personas: readonly PersonaDemo[]): PersonaDemo[] {
  const posicion = (r: RolDemo) => {
    const i = ORDEN_DE_ROLES.indexOf(r);
    return i < 0 ? ORDEN_DE_ROLES.length : i;
  };
  return [...personas].sort((a, b) => posicion(a.rol) - posicion(b.rol));
}

export function iniciales(nombre: string): string {
  return nombre
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((parte) => parte[0]?.toUpperCase() ?? "")
    .join("");
}
