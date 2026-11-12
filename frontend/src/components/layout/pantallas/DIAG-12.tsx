// ¤navegacion-menus
/**
 * Pantallas de DIAG-12 que monta el panel. Solo DIAG-12 edita este archivo.
 */
import React from "react";
import Estados from "@/components/diagnostico/Estados";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_DIAG_12: RegistroPantallas = {
  diagnostico_estados: () => <Estados />,
};
