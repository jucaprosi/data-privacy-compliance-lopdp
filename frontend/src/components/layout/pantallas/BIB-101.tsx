// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤navegacion-menus ¤adpa
/**
 * Pantalla de BIB-101 que monta el panel: Biblioteca a pantalla completa. Solo BIB-101 edita este
 * archivo. Un submenú solo se muestra si su vista tiene pantalla registrada (R4).
 */
import BibliotecaWorkspace from "@/components/biblioteca/BibliotecaWorkspace";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_BIB_101: RegistroPantallas = {
  biblioteca: () => <BibliotecaWorkspace variante="completa" />,
};
