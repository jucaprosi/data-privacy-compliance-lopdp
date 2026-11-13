// ¤navegacion-menus
// ¤riesgos-eipd
/** Pantallas de MTGE-03 que monta el panel. Solo MTGE-03 edita este archivo. */
import React from "react";
import EvaluacionesImpacto from "@/components/eipd/EvaluacionesImpacto";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_MTGE_03: RegistroPantallas = {
  eipd_guiada: () => <EvaluacionesImpacto />,
};
