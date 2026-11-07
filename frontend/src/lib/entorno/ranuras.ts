/**
 * Ranuras del aviso de entorno (EP-02). ¤entorno-pruebas
 *
 * El aviso reserva dos huecos a la derecha: `organizacion` y `acciones`. Cada ficha escribe solo
 * dentro de su sección `=== ID ===`; el componente `AvisoEntorno` no se edita para llenarlas.
 * Una ranura es una función que recibe el entorno vigente y devuelve un nodo, o `null`.
 */
import type { ReactNode } from "react";
import type { Entorno } from "@/lib/entorno";

export type NombreRanura = "organizacion" | "acciones";
export type Ranura = (entorno: Entorno) => ReactNode;
export type RegistroRanuras = Partial<Record<NombreRanura, Ranura>>;

// === DEMO-04 ===
const DEMO_04: RegistroRanuras = {};
// === fin DEMO-04 ===

const SECCIONES: readonly RegistroRanuras[] = [DEMO_04];

export function ranurasDe(nombre: NombreRanura): Ranura[] {
  return SECCIONES.map((s) => s[nombre]).filter((r): r is Ranura => typeof r === "function");
}
