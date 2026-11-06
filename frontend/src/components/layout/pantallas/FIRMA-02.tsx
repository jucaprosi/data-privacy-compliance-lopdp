// ¤navegacion-menus ¤firma-electronica
/**
 * Pantallas de FIRMA-02 que monta el panel: la lista de envíos a aceptación y la verificación de
 * documentos. Solo FIRMA-02 edita este archivo. Un submenú solo se muestra si su vista tiene
 * pantalla registrada (R4).
 */
import { EnviosAceptacion } from "@/components/firma/EnviosAceptacion";
import { VerificarDocumento } from "@/components/firma/VerificarDocumento";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_FIRMA_02: RegistroPantallas = {
  firmas: () => <EnviosAceptacion />,
  verificar_documento: () => <VerificarDocumento />,
};
