// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa
// ¤¤frontend-architect
/**
 * BIB-414 · Cliente de las capacidades editoriales del equipo (rutas de BIB-411, con la identidad de operador de BIB-412).
 * Los errores se muestran con un texto fijo por código (UX/UI §6): nunca el mensaje crudo del servidor.
 */
import { ErrorBiblioteca, httpBiblioteca } from "@/lib/biblioteca/http";
import { leerSesionDeOperador } from "@/lib/auth/sesion";
import { modoAutenticacion } from "@/lib/auth";

const BASE = "/biblioteca/capacidades/equipo";

export const CAPACIDADES_CONCEDIBLES = ["editor", "revisor_tecnico", "publicador"] as const;
export type CapacidadConcedible = (typeof CAPACIDADES_CONCEDIBLES)[number];

export interface MiembroEquipo {
  usuario_id: string; nombre: string; email: string; ha_entrado: boolean; capacidades: string[];
}
export interface EventoCapacidad {
  id: number; usuario_id: string; capacidad: string; accion: "concedida" | "retirada";
  por: string | null; motivo: string | null; en: string;
}
export type ResultadoCambio = "alta" | "reactivacion" | "vigente" | "revocacion" | "sin_vigente";

export const MOTIVO_MINIMO = 10;
export const TEXTO_PROPIA = "No puedes concederte ni retirarte capacidades a ti mismo.";
export const TEXTO_GENERICO = "No se pudo guardar. Inténtalo de nuevo.";
export const TEXTO_MOTIVO = "Escribe el motivo (al menos 10 caracteres).";
export const TEXTO_CAPACIDAD = "Elige una de las capacidades de la lista.";
export const TEXTO_VIGENTE = "Esta persona ya tiene esa capacidad.";
export const TEXTO_SIN_VIGENTE = "Esta persona no tiene esa capacidad.";

const TEXTO_POR_CODIGO: Record<string, string> = {
  BIB_SOLO_OPERADORES: "Solo el equipo de la plataforma puede conceder capacidades editoriales.",
  BIB_AUTOCONCESION: TEXTO_PROPIA,
  BIB_DESTINO_NO_OPERADOR: "Esta persona ya no es operador de la plataforma. Actualiza la lista.",
  BIB_MOTIVO_OBLIGATORIO: TEXTO_MOTIVO,
  BIB_CAPACIDAD_INVALIDA: TEXTO_CAPACIDAD,
};

/** Texto fijo de un error de las rutas del equipo; cualquier otro, el genérico. */
export function textoDeError(error: unknown): string {
  return (error instanceof ErrorBiblioteca && TEXTO_POR_CODIGO[error.codigo]) || TEXTO_GENERICO;
}

export const listarEquipo = () => httpBiblioteca<MiembroEquipo[]>(BASE);
export const listarHistorial = () => httpBiblioteca<EventoCapacidad[]>(`${BASE}/historial`);

async function cambiar(accion: "conceder" | "retirar", usuarioId: string, capacidad: string, motivo: string): Promise<ResultadoCambio> {
  const { resultado } = await httpBiblioteca<{ resultado: ResultadoCambio }>(
    `${BASE}/${encodeURIComponent(usuarioId)}/${accion}`,
    { method: "POST", body: JSON.stringify({ capacidad, motivo }) });
  return resultado;
}
export const conceder = (usuarioId: string, capacidad: string, motivo: string) => cambiar("conceder", usuarioId, capacidad, motivo);
export const retirar = (usuarioId: string, capacidad: string, motivo: string) => cambiar("retirar", usuarioId, capacidad, motivo);

/** ¿Es la persona que tiene la sesión? Por su correo en producción y por su usuario o correo en desarrollo (`headers`). */
export function esPropia(miembro: MiembroEquipo): boolean {
  const igual = (a?: string | null, b?: string | null) => !!a && !!b && a.trim().toLowerCase() === b.trim().toLowerCase();
  if (modoAutenticacion() === "oidc") return igual(miembro.email, leerSesionDeOperador()?.email);
  return igual(miembro.usuario_id, process.env.NEXT_PUBLIC_USER_ID || "operador-plataforma-dev")
    || igual(miembro.email, process.env.NEXT_PUBLIC_USER_EMAIL || "operador@plataforma.test");
}
