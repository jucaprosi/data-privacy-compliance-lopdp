// ¤navegacion-menus
// ¤controles-periodicos
/** Pantallas de CAPA-02 que monta el panel. Solo CAPA-02 edita este archivo. */
import React from "react";
import ControlesPeriodicos from "@/components/controles/ControlesPeriodicos";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_CAPA_02: RegistroPantallas = {
  controles_periodicos: () => <ControlesPeriodicos />,
};
