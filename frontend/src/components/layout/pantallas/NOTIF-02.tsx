// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤navegacion-menus
// ¤notificaciones
/** Pantalla de NOTIF-02 que monta la bandeja. Solo NOTIF-02 edita este archivo. */
import React from "react";
import BandejaAvisos from "@/components/avisos/BandejaAvisos";
import type { RegistroPantallas } from "./base";

export const PANTALLAS_NOTIF_02: RegistroPantallas = {
  avisos: () => <BandejaAvisos />,
};
