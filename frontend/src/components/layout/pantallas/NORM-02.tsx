// ¤navegacion-menus
// ¤vigilancia-spdp
/** Pantalla de NORM-02 que monta el panel. Solo NORM-02 edita este archivo. */
import React from "react";
import CentroVigilancia from "@/components/normativa/CentroVigilancia";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_NORM_02: RegistroPantallas = {
  vigilancia_normativa: () => <CentroVigilancia />,
};
