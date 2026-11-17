// ¤navegacion-menus ¤api-integraciones
/**
 * Pantallas de API-02 que monta el panel.
 */
import React from "react";
import IntegracionesView from "@/components/integraciones/IntegracionesView";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_API_02: RegistroPantallas = {
  integraciones: () => <IntegracionesView />,
};
