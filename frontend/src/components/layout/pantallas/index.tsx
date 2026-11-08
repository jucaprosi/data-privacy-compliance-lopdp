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

// === BIB-101 ===
import { PANTALLAS_BIB_101 } from "./BIB-101";
registrar(PANTALLAS_BIB_101);
// === fin BIB-101 ===

// === REG-02 ===
import { PANTALLAS_REG_02 } from "./REG-02";
registrar(PANTALLAS_REG_02);
// === fin REG-02 ===

// === FIRMA-02 ===
import { PANTALLAS_FIRMA_02 } from "./FIRMA-02";
registrar(PANTALLAS_FIRMA_02);
// === fin FIRMA-02 ===
// --- INICIO CAPA-04 ---
// --- FIN CAPA-04 ---
// --- INICIO DIAG-07 ---
// --- FIN DIAG-07 ---
// --- INICIO DPO-03 ---
// --- FIN DPO-03 ---
// --- INICIO FIRMA-02 ---
// --- FIN FIRMA-02 ---
// --- INICIO FOR-01 ---
// --- FIN FOR-01 ---
// --- INICIO INC-02 ---
// --- FIN INC-02 ---
// --- INICIO MTGE-03 ---
// --- FIN MTGE-03 ---
// --- INICIO ORG-18 ---
// --- FIN ORG-18 ---
// --- INICIO ORG-20 ---
// --- FIN ORG-20 ---
// --- INICIO CON-01 ---
// --- FIN CON-01 ---

export const PANTALLAS: Readonly<RegistroPantallas> = registro;

// === BIB-118 ===
// === fin BIB-118 ===
