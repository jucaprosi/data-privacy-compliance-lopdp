// ¤boveda-cloud ¤evidencias ¤adpa
import React, { useState } from "react";
import type { Pantalla, RegistroPantallas } from "./base";

export function PantallaBov03() {
  const [verificado, setVerificado] = useState(true);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-[var(--ui-borde)] pb-4">
        <div>
          <h2 className="text-lg font-bold">Bóveda Cloud · Carril Forense Dual (BOV-03)</h2>
          <p className="text-xs text-[var(--ui-texto-suave)]">
            Custodia del original intacto SHA-256 y previsualizaciones optimizadas WebP/WebM.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {verificado ? (
            <span className="badge-render-success px-2.5 py-1 rounded text-xs font-semibold">
              SHA-256 Verificado Intacto
            </span>
          ) : (
            <span className="badge-render-danger px-2.5 py-1 rounded text-xs font-semibold">
              Alteración Detectada
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-4 rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] space-y-3">
          <h3 className="text-sm font-semibold">Vista Previa Optimizada (WebP / WebM)</h3>
          <p className="text-xs text-[var(--ui-texto-suave)]">
            Carga rápida sin consumo de egress del original probatorio.
          </p>
          <div className="aspect-video rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-campo)] flex items-center justify-center text-xs text-[var(--ui-texto-suave)]">
            Vista previa ligera derivada
          </div>
        </div>

        <div className="p-4 rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] space-y-3">
          <h3 className="text-sm font-semibold">Custodia Forense del Original</h3>
          <p className="text-xs text-[var(--ui-texto-suave)]">
            Archivo primario inalterado para inspección judicial o de la SPDP.
          </p>
          <div className="p-3 rounded-lg bg-[var(--ui-campo)] font-mono text-xs break-all">
            Hash SHA-256 original inmutable
          </div>
          <button
            type="button"
            className="px-3 py-1.5 rounded-lg bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] text-xs font-semibold hover:bg-[var(--ui-primario-hover)] cursor-pointer"
          >
            Descargar original certificado
          </button>
        </div>
      </div>
    </div>
  );
}

export const PANTALLAS_BOV_03: Record<string, Pantalla> = {
  boveda_forense: () => <PantallaBov03 />,
};
