"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Anfitrión de pruebas para la ranura `plantilla:acciones` (BIB-104).
 * Permite a Playwright verificar el botón de descarga y la ranura de acciones.
 */
import React from "react";
import {
  registrarVista,
  useSeleccionBiblioteca,
  vistasDe,
  type PropsVistaBiblioteca,
} from "@/lib/biblioteca/registro";

declare global {
  interface Window {
    __LOPDP_DESCARGA_PRUEBAS__?: { plantillaId: string };
  }
}

function Anfitrion({ variante }: PropsVistaBiblioteca) {
  const elegir = useSeleccionBiblioteca((s) => s.elegirPlantilla);
  const id = typeof window === "undefined" ? undefined : window.__LOPDP_DESCARGA_PRUEBAS__?.plantillaId;
  React.useEffect(() => {
    if (id) elegir(id);
  }, [id, elegir]);

  return (
    <div data-testid="anfitrion-descargas">
      {vistasDe("plantilla:acciones").map((Vista, i) => (
        <Vista key={i} variante={variante} />
      ))}
    </div>
  );
}

if (process.env.NODE_ENV !== "production" && typeof window !== "undefined" && window.__LOPDP_DESCARGA_PRUEBAS__) {
  registrarVista("pestana:plantillas", Anfitrion);
}
