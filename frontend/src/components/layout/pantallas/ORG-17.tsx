// ¤navegacion-menus
/**
 * Pantalla de ORG-17 que monta el panel: el inventario de activos, soportes y personas. Solo ORG-17
 * edita este archivo. Un submenú solo se muestra si su vista tiene pantalla registrada (R4).
 */
import InventarioPantalla from "@/components/organizacion/inventario/InventarioPantalla";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_ORG_17: RegistroPantallas = {
  inventario_activos: () => <InventarioPantalla />,
};
