"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Anfitrión de pruebas para formularios y editor de borrador (BIB-114).
 *
 * Permite que los tests E2E monten las ranuras `plantilla:acciones` y `documento:editor`
 * en las pestañas correspondientes mediante `window.__LOPDP_FORMULARIOS_PRUEBAS__`.
 * Fuera de desarrollo/test (`NODE_ENV === "production"`), este bloque se elimina por completo.
 */
import React from "react";
import { registrarVista, useSeleccionBiblioteca, vistasDe, type PropsVistaBiblioteca } from "@/lib/biblioteca/registro";

export interface ConfigFormulariosPruebas {
  plantillaId?: string;
  documentoId?: string;
  ranura?: "plantilla:acciones" | "documento:editor";
}

declare global {
  interface Window {
    __LOPDP_FORMULARIOS_PRUEBAS__?: ConfigFormulariosPruebas;
  }
}

function AnfitrionPlantillaAcciones({ variante }: PropsVistaBiblioteca) {
  const storeId = useSeleccionBiblioteca((s) => s.plantillaId);
  const elegir = useSeleccionBiblioteca((s) => s.elegirPlantilla);
  const cfg = typeof window !== "undefined" ? window.__LOPDP_FORMULARIOS_PRUEBAS__ : undefined;

  React.useEffect(() => {
    if (cfg?.plantillaId && storeId !== cfg.plantillaId) {
      elegir(cfg.plantillaId);
    }
  }, [cfg?.plantillaId, storeId, elegir]);

  return (
    <div data-testid="anfitrion-plantilla-acciones" className="flex flex-col gap-3">
      {vistasDe("plantilla:acciones").map((Vista, i) => (
        <Vista key={i} variante={variante} />
      ))}
    </div>
  );
}

function AnfitrionDocumentoEditor({ variante }: PropsVistaBiblioteca) {
  const storeId = useSeleccionBiblioteca((s) => s.documentoId);
  const elegir = useSeleccionBiblioteca((s) => s.elegirDocumento);
  const cfg = typeof window !== "undefined" ? window.__LOPDP_FORMULARIOS_PRUEBAS__ : undefined;

  React.useEffect(() => {
    if (cfg?.documentoId && storeId !== cfg.documentoId) {
      elegir(cfg.documentoId);
    }
  }, [cfg?.documentoId, storeId, elegir]);

  return (
    <div data-testid="anfitrion-documento-editor" className="flex flex-col gap-3">
      {vistasDe("documento:editor").map((Vista, i) => (
        <Vista key={i} variante={variante} />
      ))}
    </div>
  );
}

if (process.env.NODE_ENV !== "production" && typeof window !== "undefined" && window.__LOPDP_FORMULARIOS_PRUEBAS__) {
  const config = window.__LOPDP_FORMULARIOS_PRUEBAS__;
  if (config.ranura === "plantilla:acciones" || config.plantillaId) {
    registrarVista("pestana:plantillas", AnfitrionPlantillaAcciones);
  }
  if (config.ranura === "documento:editor" || config.documentoId) {
    registrarVista("pestana:documentos", AnfitrionDocumentoEditor);
  }
}
