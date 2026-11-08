// ¤adpa
// ¤¤frontend-architect
/**
 * BIB-118 · Contexto de visibilidad del menú: `null` mientras carga, luego la lista (vacía si falla).
 *
 * Un solo almacén por pestaña: la paleta (en el layout raíz) se suscribe con el hook y el panel lee el
 * valor vigente con `contextoVisibilidad()`. La primera lectura dispara la carga.
 */
"use client";
import { useSyncExternalStore } from "react";
import { leerMisCapacidades } from "@/lib/biblioteca/capacidadesEditoriales";

export interface ContextoCapacidades {
  capacidadesEditoriales: readonly string[] | null;
}

const CARGANDO: ContextoCapacidades = { capacidadesEditoriales: null };
let actual: ContextoCapacidades = CARGANDO;
let pedida = false;
const oyentes = new Set<() => void>();

function cargar(): void {
  if (pedida || typeof window === "undefined") return;
  pedida = true;
  void leerMisCapacidades().then((lista) => {
    actual = { capacidadesEditoriales: lista };
    oyentes.forEach((avisar) => avisar());
  });
}

/** Valor vigente sin suscribirse; útil donde no se puede llamar a un hook. */
export function contextoVisibilidad(): ContextoCapacidades {
  cargar();
  return actual;
}

export function useCapacidadesEditoriales(): ContextoCapacidades {
  return useSyncExternalStore(
    (avisar) => { oyentes.add(avisar); cargar(); return () => { oyentes.delete(avisar); }; },
    () => actual,
    () => CARGANDO,
  );
}
