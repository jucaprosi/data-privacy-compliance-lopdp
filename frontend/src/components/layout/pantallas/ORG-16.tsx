// ¤navegacion-menus
/**
 * Pantalla de ORG-16 que monta el panel: el alta de la organización. Solo ORG-16 edita este archivo.
 * Un submenú solo se muestra si su vista tiene pantalla registrada (R4).
 */
import AltaPantalla from "@/components/organizacion/alta/AltaPantalla";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_ORG_16: RegistroPantallas = {
  alta_organizacion: () => <AltaPantalla />,
};
