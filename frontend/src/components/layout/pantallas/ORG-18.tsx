// ¤navegacion-menus
/**
 * Pantallas de ORG-18 que monta el panel: sedes y clientes por encargo. Solo ORG-18 edita este archivo.
 * Un submenú solo se muestra si su vista tiene pantalla registrada (R4).
 */
import ClientesPantalla from "@/components/organizacion/sedes/ClientesPantalla";
import SedesPantalla from "@/components/organizacion/sedes/SedesPantalla";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_ORG_18: RegistroPantallas = {
  sedes_organizacion: () => <SedesPantalla />,
  clientes_encargo: () => <ClientesPantalla />,
};
