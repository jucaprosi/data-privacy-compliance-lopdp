"use client";

import * as React from "react";

import { modoAutenticacion } from "./modo";
import { cerrarSesion, leerSesion, suscribirSesion, type Sesion } from "./sesion";

export interface EstadoSesion {
  /** False hasta leer el almacenamiento del navegador (el servidor no lo tiene). */
  listo: boolean;
  /** "headers" no pide inicio de sesión. */
  requiereSesion: boolean;
  sesion: Sesion | null;
}

/** Sesión actual y reacción a cierre, inicio y caducidad (el token vence solo, sin esperar un 401). */
export function useSesion(): EstadoSesion {
  const [listo, setListo] = React.useState(false);
  const [sesion, setSesion] = React.useState<Sesion | null>(null);

  React.useEffect(() => {
    setSesion(leerSesion());
    setListo(true);
    return suscribirSesion(setSesion);
  }, []);

  React.useEffect(() => {
    if (!sesion) return;
    const faltanMs = sesion.exp * 1000 - Date.now();
    const temporizador = window.setTimeout(cerrarSesion, Math.max(faltanMs, 0));
    return () => window.clearTimeout(temporizador);
  }, [sesion]);

  return { listo, requiereSesion: modoAutenticacion() === "oidc", sesion };
}
