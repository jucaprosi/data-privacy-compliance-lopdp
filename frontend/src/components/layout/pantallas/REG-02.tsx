// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤navegacion-menus
/** Pantallas de REG-02 que monta el panel (menú Conocimiento). Un submenú solo se muestra si su vista está aquí (R4). */
import React from "react";
import type { RegistroPantallas } from "./base";
import NormativaEcuadorView from "@/components/conocimiento/NormativaEcuadorView";
import ResumenesGuiasView from "@/components/conocimiento/ResumenesGuiasView";
import AyudaView from "@/components/conocimiento/AyudaView";

export const PANTALLAS_REG_02: RegistroPantallas = {
  normativa_ecuador: () => <NormativaEcuadorView />,
  resumenes_guias: () => <ResumenesGuiasView />,
  ayuda_conocimiento: () => <AyudaView />,
};
