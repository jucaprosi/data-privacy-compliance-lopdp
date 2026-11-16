// ¤navegacion-menus
/**
 * Pantalla de ORG-15 que monta el panel: el tablero de cartera. Solo ORG-15 edita este archivo.
 * Un submenú solo se muestra si su vista tiene pantalla registrada (R4).
 */
import CarteraTablero from "@/app/cartera/CarteraTablero";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_ORG_15: RegistroPantallas = {
  cartera: () => <CarteraTablero />,
};
