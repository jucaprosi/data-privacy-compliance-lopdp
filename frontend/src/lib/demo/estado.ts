/**
 * Estado del navegador para la demo (DEMO-04). ¤demo
 *
 * Guarda la persona que devolvió el servidor (la interfaz nunca la fija por su cuenta) y avisa
 * cuando la sesión de demo venció. Por pestaña (`sessionStorage`): cada pestaña es su propia entrada.
 */
import type { RolDemo } from "./contrato";

const CLAVE_PERSONA = "evydentia.demo.persona";
const CLAVE_BIENVENIDA = "evydentia.demo.bienvenida";

export interface PersonaActiva {
  usuario_id: string;
  rol: RolDemo;
}

function almacen(): Storage | null {
  try {
    return typeof window !== "undefined" ? window.sessionStorage : null;
  } catch {
    return null;
  }
}

export function leerPersonaActiva(): PersonaActiva | null {
  const bruto = almacen()?.getItem(CLAVE_PERSONA);
  if (!bruto) return null;
  try {
    const p = JSON.parse(bruto) as PersonaActiva;
    return typeof p?.rol === "string" && typeof p?.usuario_id === "string" ? p : null;
  } catch {
    return null;
  }
}

export function guardarPersonaActiva(p: PersonaActiva): void {
  almacen()?.setItem(CLAVE_PERSONA, JSON.stringify({ usuario_id: p.usuario_id, rol: p.rol }));
}

export function olvidarPersonaActiva(): void {
  almacen()?.removeItem(CLAVE_PERSONA);
}

export function marcarBienvenida(): void {
  almacen()?.setItem(CLAVE_BIENVENIDA, "1");
}

/** Devuelve true una sola vez tras la entrada. */
export function tomarBienvenida(): boolean {
  const a = almacen();
  if (a?.getItem(CLAVE_BIENVENIDA) !== "1") return false;
  a.removeItem(CLAVE_BIENVENIDA);
  return true;
}

// Aviso de vencimiento: lo emite el interceptor de fetchAutenticado y lo escucha la pantalla.
type Oyente = () => void;
const oyentes = new Set<Oyente>();
let vencida = false;

export function avisarDemoVencida(): void {
  vencida = true;
  olvidarPersonaActiva();
  oyentes.forEach((o) => o());
}

export function demoVencida(): boolean {
  return vencida;
}

export function alVencerLaDemo(oyente: Oyente): () => void {
  oyentes.add(oyente);
  return () => {
    oyentes.delete(oyente);
  };
}
