// ¤navegacion-menus
// ¤diagnostico-asignacion
/** Pantallas de DIAG-04 que monta el panel. Solo DIAG-04 edita este archivo. */
import React from "react";
import AsignacionDominios from "@/components/diagnostico/AsignacionDominios";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_DIAG_04: RegistroPantallas = {
  asignacion_dominios: () => <AsignacionDominios />,
};
