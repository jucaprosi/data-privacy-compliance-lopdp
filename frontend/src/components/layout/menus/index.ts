// ¤¤frontend-architect
// ¤navegacion-menus
/**
 * Registro de submenús de los nueve menús (FE-22).
 *
 * Registro por archivo, no por sección compartida: cada tarea que añade submenús escribe solo su
 * `menus/<ID>.ts`. Las seis tareas previstas ya están registradas abajo y no vuelven a tocar este
 * archivo. Una tarea que aparezca después añade su propia sección, entre las marcas
 * `// === <ID> ===` y `// === fin <ID> ===`, con su `import` y su `registrar(...)`; esa sección
 * es lo único que posee de este archivo.
 */
import { MENUS, SUBMENUS_BASE, type Submenu } from "./base";

export { MENUS };
export type { Menu, MenuId, Submenu } from "./base";

const registro: Submenu[] = [];

function registrar(submenus: readonly Submenu[]): void {
  registro.push(...submenus);
}

registrar(SUBMENUS_BASE);

// === ORG-15 ===
import { SUBMENUS_ORG_15 } from "./ORG-15";
registrar(SUBMENUS_ORG_15);
// === fin ORG-15 ===

// === ORG-16 ===
import { SUBMENUS_ORG_16 } from "./ORG-16";
registrar(SUBMENUS_ORG_16);
// === fin ORG-16 ===

// === ORG-17 ===
import { SUBMENUS_ORG_17 } from "./ORG-17";
registrar(SUBMENUS_ORG_17);
// === fin ORG-17 ===

// === CAPA-02 ===
import { SUBMENUS_CAPA_02 } from "./CAPA-02";
registrar(SUBMENUS_CAPA_02);
// === fin CAPA-02 ===

// === DIAG-04 ===
import { SUBMENUS_DIAG_04 } from "./DIAG-04";
registrar(SUBMENUS_DIAG_04);
// === fin DIAG-04 ===

// === DIAG-06 ===
import { SUBMENUS_DIAG_06 } from "./DIAG-06";
registrar(SUBMENUS_DIAG_06);
// === fin DIAG-06 ===

/**
 * R3 · Unicidad: una vista pertenece a un solo submenú. Un submenú repetido detiene la carga del
 * módulo, de modo que fallan la compilación de la aplicación y las pruebas que lo importan.
 */
function comprobarUnicidad(submenus: readonly Submenu[]): Submenu[] {
  const vistas = new Set<string>();
  for (const s of submenus) {
    if (vistas.has(s.vista)) throw new Error(`Submenú repetido para la vista «${s.vista}» (FE-22, R3).`);
    vistas.add(s.vista);
  }
  return [...submenus].sort(
    (a, b) =>
      (MENUS.find((m) => m.id === a.menu)?.orden ?? 99) - (MENUS.find((m) => m.id === b.menu)?.orden ?? 99) ||
      a.orden - b.orden
  );
}

/** Todos los submenús: `base.ts` más cada `menus/<ID>.ts`, ordenados por menú y por orden. */
export const SUBMENUS: Submenu[] = comprobarUnicidad(registro);
