// ¤adpa
// ¤¤frontend-architect
/**
 * BIB-118/BIB-119 · Contexto de visibilidad del menú: `null` mientras carga, luego la lista.
 *
 * Un almacén por pestaña con clave `email | X-Tenant-ID | persona activa` (la persona solo existe en la
 * demo). La clave se recalcula al leer: si cambió, el valor vuelve a `null`, se pide `/mias` otra vez y
 * sube la generación; la respuesta de una generación vieja se descarta. Sin sesión (en "oidc") la lista
 * es `[]` y no se llama al servidor. Si la petición falla, la lista es `[]` con `fallo: true`.
 * Solo lee `lib/auth` y `lib/demo/estado`.
 */
"use client";
import { useSyncExternalStore } from "react";
import { cabecerasDeTenant, leerSesion, modoAutenticacion, suscribirSesion } from "@/lib/auth";
import { leerPersonaActiva } from "@/lib/demo/estado";
import { httpBiblioteca } from "@/lib/biblioteca/http";

export interface ContextoCapacidades {
  capacidadesEditoriales: readonly string[] | null;
  /** La última petición falló: la lista vacía no significa «sin permisos». */
  fallo?: boolean;
}

const CARGANDO: ContextoCapacidades = { capacidadesEditoriales: null };
const SIN_SESION: ContextoCapacidades = { capacidadesEditoriales: [] };
let actual: ContextoCapacidades = CARGANDO;
let clave: string | null | undefined;
let generacion = 0;
const oyentes = new Set<() => void>();
let desuscribirSesion: (() => void) | null = null;

function avisar(): void {
  oyentes.forEach((oyente) => oyente());
}

function claveActual(): string | null {
  const sesion = leerSesion();
  if (modoAutenticacion() === "oidc" && !sesion) return null;
  const tenant = cabecerasDeTenant()["X-Tenant-ID"] ?? "";
  return `${sesion?.email ?? ""}|${tenant}|${leerPersonaActiva()?.usuario_id ?? ""}`;
}

async function pedir(): Promise<ContextoCapacidades> {
  try {
    const { capacidades } = await httpBiblioteca<{ capacidades: string[] }>("/biblioteca/capacidades/mias");
    return { capacidadesEditoriales: Array.isArray(capacidades) ? capacidades : [] };
  } catch {
    return { capacidadesEditoriales: [], fallo: true };
  }
}

/** Recalcula la clave; si cambió, reinicia y vuelve a pedir. Devuelve si cambió. */
function sincronizar(): boolean {
  if (typeof window === "undefined") return false;
  const nueva = claveActual();
  if (nueva === clave) return false;
  clave = nueva;
  const propia = ++generacion;
  if (nueva === null) {
    actual = SIN_SESION;
  } else {
    actual = CARGANDO;
    void pedir().then((resultado) => {
      if (propia !== generacion) return;  // respuesta de otra persona u organización
      actual = resultado;
      avisar();
    });
  }
  return true;
}

function leer(): ContextoCapacidades {
  if (sincronizar()) queueMicrotask(avisar);
  return actual;
}

/** Valor vigente sin suscribirse. */
export function contextoVisibilidad(): ContextoCapacidades {
  return leer();
}

function suscribir(oyente: () => void): () => void {
  oyentes.add(oyente);
  desuscribirSesion ??= suscribirSesion(() => { if (sincronizar()) avisar(); });
  return () => {
    oyentes.delete(oyente);
    if (oyentes.size === 0 && desuscribirSesion) { desuscribirSesion(); desuscribirSesion = null; }
  };
}

export function useCapacidadesEditoriales(): ContextoCapacidades {
  return useSyncExternalStore(suscribir, leer, () => CARGANDO);
}
