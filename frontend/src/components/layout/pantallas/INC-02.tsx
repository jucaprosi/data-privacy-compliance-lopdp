// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤navegacion-menus
// ¤incidentes
/** Pantalla de INC-02 que monta el panel. Solo INC-02 edita este archivo. */
import React from "react";
import AsistenteVulneraciones from "@/components/incidentes/AsistenteVulneraciones";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_INC_02: RegistroPantallas = {
  asistente_vulneraciones: () => <AsistenteVulneraciones />,
};
