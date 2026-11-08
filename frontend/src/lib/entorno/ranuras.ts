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
import { createElement } from "react";
import AccionesDemo, { OrganizacionDemo } from "@/components/demo/AccionesDemo";

/** Solo en `demo`; cada componente vuelve a confirmar con `GET /api/v1/entorno` y `/demo/estado`. */
const DEMO_04: RegistroRanuras = {
  organizacion: (entorno) => (entorno === "demo" ? createElement(OrganizacionDemo) : null),
  acciones: (entorno) => (entorno === "demo" ? createElement(AccionesDemo) : null),
};
// === fin DEMO-04 ===

const SECCIONES: readonly RegistroRanuras[] = [DEMO_04];

export function ranurasDe(nombre: NombreRanura): Ranura[] {
  return SECCIONES.map((s) => s[nombre]).filter((r): r is Ranura => typeof r === "function");
}
