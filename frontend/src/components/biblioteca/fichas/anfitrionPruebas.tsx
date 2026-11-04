"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Anfitrión de pruebas de la ficha (BIB-103): hasta que el catálogo (BIB-102) pinte la ranura `plantilla:ficha`,
 * `ficha.spec.ts` fija `window.__LOPDP_FICHA_PRUEBAS__ = { plantillaId }` desde el navegador y este anfitrión se monta en
 * la pestaña Plantillas, elige esa plantilla y pinta las vistas de la ranura. Sin ese gancho no hace nada, y en un build de
 * producción `NODE_ENV` es una constante y el bloque se elimina.
 */
import React from "react";
import { registrarVista, useSeleccionBiblioteca, vistasDe, type PropsVistaBiblioteca } from "@/lib/biblioteca/registro";

declare global {
  interface Window { __LOPDP_FICHA_PRUEBAS__?: { plantillaId: string } }
}

function Anfitrion({ variante }: PropsVistaBiblioteca) {
  const elegir = useSeleccionBiblioteca((s) => s.elegirPlantilla);
  const id = typeof window === "undefined" ? undefined : window.__LOPDP_FICHA_PRUEBAS__?.plantillaId;
  React.useEffect(() => { if (id) elegir(id); }, [id, elegir]);
  return <>{vistasDe("plantilla:ficha").map((Vista, i) => <Vista key={i} variante={variante} />)}</>;
}

if (process.env.NODE_ENV !== "production" && typeof window !== "undefined" && window.__LOPDP_FICHA_PRUEBAS__) {
  registrarVista("pestana:plantillas", Anfitrion);
}
