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

// === DIAG-12 ===
import { SUBMENUS_DIAG_12 } from "./DIAG-12";
registrar(SUBMENUS_DIAG_12);
// === fin DIAG-12 ===

// === BIB-101 ===
import { SUBMENUS_BIB_101 } from "./BIB-101";
registrar(SUBMENUS_BIB_101);
// === fin BIB-101 ===

// === REG-02 ===
import { SUBMENUS_REG_02 } from "./REG-02";
registrar(SUBMENUS_REG_02);
// === fin REG-02 ===

// === FIRMA-02 ===
import { SUBMENUS_FIRMA_02 } from "./FIRMA-02";
registrar(SUBMENUS_FIRMA_02);
// === fin FIRMA-02 ===
// --- INICIO CAPA-04 ---
// --- FIN CAPA-04 ---
// --- INICIO DIAG-07 ---
// --- FIN DIAG-07 ---
// --- INICIO DPO-03 ---
import { SUBMENUS_DPO_03 } from "./DPO-03";
registrar(SUBMENUS_DPO_03);
// --- FIN DPO-03 ---
// --- INICIO FIRMA-02 ---
// --- FIN FIRMA-02 ---
// --- INICIO API-02 ---
// --- FIN API-02 ---
// --- INICIO FOR-01 ---
// --- FIN FOR-01 ---
// --- INICIO INC-02 ---
// --- FIN INC-02 ---
// --- INICIO MTGE-03 ---
import { SUBMENUS_MTGE_03 } from "./MTGE-03";
registrar(SUBMENUS_MTGE_03);
// --- FIN MTGE-03 ---
// --- INICIO ORG-18 ---
import { SUBMENUS_ORG_18 } from "./ORG-18";
registrar(SUBMENUS_ORG_18);
// --- FIN ORG-18 ---
// --- INICIO ORG-20 ---
import { SUBMENUS_ORG_20 } from "./ORG-20";
registrar(SUBMENUS_ORG_20);
// --- FIN ORG-20 ---
// --- INICIO CON-01 ---
// --- FIN CON-01 ---

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

// === BIB-118 ===
// Esta sección va después de `SUBMENUS`: añade el submenú y vuelve a comprobar unicidad y orden en el mismo arreglo.
import { SUBMENUS_BIB_118 } from "./BIB-118";
export type { ContextoVisibilidad } from "./base";
export { CONTEXTO_VACIO } from "./base";
SUBMENUS.splice(0, SUBMENUS.length, ...comprobarUnicidad([...SUBMENUS, ...SUBMENUS_BIB_118]));
// === fin BIB-118 ===

// === ORG-20 ===
// Sección reservada para ORG-20.
// === fin ORG-20 ===

// === DLP-01 ===
declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    descubrimiento_datos: true;
  }
}
const SUBMENUS_DLP_01: Submenu[] = [
  {
    vista: "descubrimiento_datos",
    menu: "inventario",
    nombre: "Descubrimiento de datos",
    subtitulo: "Detecta tipos de datos personales en una muestra",
    orden: 6,
  },
];
SUBMENUS.splice(0, SUBMENUS.length, ...comprobarUnicidad([...SUBMENUS, ...SUBMENUS_DLP_01]));
// === fin DLP-01 ===

// === NORM-02 ===
// Sección reservada para NORM-02.
// === fin NORM-02 ===
