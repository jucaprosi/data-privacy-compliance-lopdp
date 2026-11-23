// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤navegacion-menus
/**
 * Pantallas de DIAG-06 que monta el panel. Solo DIAG-06 edita este archivo.
 */
import React from "react";
import Comparativo from "@/components/diagnostico/Comparativo";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_DIAG_06: RegistroPantallas = {
  diagnostico_comparativo: () => <Comparativo />,
};
