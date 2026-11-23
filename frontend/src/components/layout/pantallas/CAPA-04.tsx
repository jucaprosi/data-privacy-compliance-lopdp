// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤navegacion-menus ¤auditoria-capa ¤hallazgos
/**
 * Pantallas de CAPA-04 que monta el dashboard.
 */
import React from "react";
import { AuditoriasView } from "@/components/auditoria/AuditoriasView";
import type { RegistroPantallas } from "./base";
import { PANTALLAS_BASE } from "./base";

export const PANTALLAS_CAPA_04: RegistroPantallas = {
  auditoria: (contexto) => (
    <div className="space-y-8">
      {PANTALLAS_BASE.auditoria?.(contexto)}
      <AuditoriasView />
    </div>
  ),
};
