// ¤navegacion-menus
// ¤riesgos-eipd
/**
 * Pantallas de MTGE-03. Solo MTGE-03 edita este archivo.
 * La EIPD guiada vive en Riesgos y auditoría › Evaluaciones de impacto (origen de la ficha): se suma a la
 * calificación de gran escala de esa vista, sin submenú nuevo, para no alterar el dock ni la paleta de FE-22.
 */
import React from "react";
import MtgeRelacionalModule from "@/components/modules/MtgeRelacionalModule";
import EvaluacionesImpacto from "@/components/eipd/EvaluacionesImpacto";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_MTGE_03: RegistroPantallas = {
  mtge_relacional: () => (
    <div className="flex min-w-0 flex-col gap-8">
      <MtgeRelacionalModule />
      <EvaluacionesImpacto />
    </div>
  ),
};
