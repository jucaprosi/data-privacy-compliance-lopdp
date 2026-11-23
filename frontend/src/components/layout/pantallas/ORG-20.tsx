// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤navegacion-menus
/**
 * Pantallas de ORG-20: la papelera y la exportación de los datos de la organización. Solo ORG-20 edita este
 * archivo. Un submenú solo se muestra si su vista tiene pantalla registrada (R4).
 */
import ExportarDatosPantalla from "@/components/organizacion/papelera/ExportarDatosPantalla";
import PapeleraPantalla from "@/components/organizacion/papelera/PapeleraPantalla";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_ORG_20: RegistroPantallas = {
  papelera: () => <PapeleraPantalla />,
  exportar_datos: () => <ExportarDatosPantalla />,
};
