// ¤navegacion-menus
// ¤dpo-cockpit
/** Pantallas de DPO-03 que monta el panel. Solo DPO-03 edita este archivo. */
import React from "react";
import Consultas from "@/components/dpo/Consultas";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_DPO_03: RegistroPantallas = {
  consultas_dpo_mias: () => <Consultas modo="mias" />,
  consultas_dpo_atendidas: () => <Consultas modo="atendidas" />,
};
