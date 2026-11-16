// ¤navegacion-menus ¤auditoria-capa ¤hallazgos
/**
 * Pantallas de CAPA-04 que monta el dashboard.
 */
import React from "react";
import { AuditoriasView } from "@/components/auditoria/AuditoriasView";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_CAPA_04: RegistroPantallas = {
  capa04_auditorias: () => <AuditoriasView />,
};
