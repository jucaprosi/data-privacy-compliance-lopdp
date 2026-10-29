// ¤¤frontend-architect
// ¤navegacion-menus
/**
 * Registro de pantallas del panel (FE-22).
 *
 * Mismo patrón que `menus/index.ts`: cada tarea escribe solo su `pantallas/<ID>.tsx`. Las seis
 * tareas previstas ya están registradas abajo y no vuelven a tocar este archivo. Una tarea que
 * aparezca después añade su propia sección, entre `// === <ID> ===` y `// === fin <ID> ===`, con
 * su `import` y su `registrar(...)`.
 *
 * R4 · Un submenú se muestra solo si su vista tiene pantalla aquí.
 */
import { PANTALLAS_BASE, type RegistroPantallas } from "./base";

export type { ContextoPantalla, Pantalla, RegistroPantallas } from "./base";

const registro: RegistroPantallas = {};

function registrar(pantallas: RegistroPantallas): void {
  Object.assign(registro, pantallas);
}

registrar(PANTALLAS_BASE);

// === ORG-15 ===
import { PANTALLAS_ORG_15 } from "./ORG-15";
registrar(PANTALLAS_ORG_15);
// === fin ORG-15 ===

// === ORG-16 ===
import { PANTALLAS_ORG_16 } from "./ORG-16";
registrar(PANTALLAS_ORG_16);
// === fin ORG-16 ===

// === ORG-17 ===
import { PANTALLAS_ORG_17 } from "./ORG-17";
registrar(PANTALLAS_ORG_17);
// === fin ORG-17 ===

// === CAPA-02 ===
import { PANTALLAS_CAPA_02 } from "./CAPA-02";
registrar(PANTALLAS_CAPA_02);
// === fin CAPA-02 ===

// === DIAG-04 ===
import { PANTALLAS_DIAG_04 } from "./DIAG-04";
registrar(PANTALLAS_DIAG_04);
// === fin DIAG-04 ===

// === DIAG-06 ===
import { PANTALLAS_DIAG_06 } from "./DIAG-06";
registrar(PANTALLAS_DIAG_06);
// === fin DIAG-06 ===

export const PANTALLAS: Readonly<RegistroPantallas> = registro;
