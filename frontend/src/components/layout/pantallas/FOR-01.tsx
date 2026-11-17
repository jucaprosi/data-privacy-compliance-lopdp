// ¤navegacion-menus ¤formacion
/**
 * Pantallas de FOR-01 que monta el dashboard: Formación (gestión) y Mi formación (participante).
 */
import React, { useState } from "react";
import type { RegistroPantallas } from "./base";
import { CoberturaTarjeta } from "@/components/formacion/CoberturaTarjeta";
import { AccionesPanel } from "@/components/formacion/AccionesPanel";
import { ContenidosPanel } from "@/components/formacion/ContenidosPanel";
import { MiFormacion } from "@/components/formacion/MiFormacion";

const FormacionGestion: React.FC = () => {
  const [tabActiva, setTabActiva] = useState<"cobertura" | "acciones" | "contenidos">("cobertura");

  return (
    <main aria-label="Formación" className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--ui-text-primary)]">Formación</h1>
        <p className="text-sm text-[var(--ui-text-secondary)] mt-1">
          Contenidos, capacitaciones y avance del plan de formación.
        </p>
      </div>

      <div role="tablist" aria-label="Formación" className="flex border-b border-[var(--ui-border)] space-x-4">
        <button
          role="tab"
          aria-selected={tabActiva === "cobertura"}
          aria-controls="panel-cobertura"
          id="tab-cobertura"
          onClick={() => setTabActiva("cobertura")}
          className={`pb-2 px-1 text-sm font-semibold transition-colors border-b-2 ${
            tabActiva === "cobertura"
              ? "border-[var(--ui-primary)] text-[var(--ui-primary)]"
              : "border-transparent text-[var(--ui-text-secondary)] hover:text-[var(--ui-text-primary)]"
          }`}
        >
          Cobertura
        </button>
        <button
          role="tab"
          aria-selected={tabActiva === "acciones"}
          aria-controls="panel-acciones"
          id="tab-acciones"
          onClick={() => setTabActiva("acciones")}
          className={`pb-2 px-1 text-sm font-semibold transition-colors border-b-2 ${
            tabActiva === "acciones"
              ? "border-[var(--ui-primary)] text-[var(--ui-primary)]"
              : "border-transparent text-[var(--ui-text-secondary)] hover:text-[var(--ui-text-primary)]"
          }`}
        >
          Acciones
        </button>
        <button
          role="tab"
          aria-selected={tabActiva === "contenidos"}
          aria-controls="panel-contenidos"
          id="tab-contenidos"
          onClick={() => setTabActiva("contenidos")}
          className={`pb-2 px-1 text-sm font-semibold transition-colors border-b-2 ${
            tabActiva === "contenidos"
              ? "border-[var(--ui-primary)] text-[var(--ui-primary)]"
              : "border-transparent text-[var(--ui-text-secondary)] hover:text-[var(--ui-text-primary)]"
          }`}
        >
          Contenidos
        </button>
      </div>

      <div className="pt-2">
        {tabActiva === "cobertura" && (
          <div role="tabpanel" id="panel-cobertura" aria-labelledby="tab-cobertura">
            <CoberturaTarjeta />
          </div>
        )}
        {tabActiva === "acciones" && (
          <div role="tabpanel" id="panel-acciones" aria-labelledby="tab-acciones">
            <AccionesPanel puedeGestionar={true} />
          </div>
        )}
        {tabActiva === "contenidos" && (
          <div role="tabpanel" id="panel-contenidos" aria-labelledby="tab-contenidos">
            <ContenidosPanel puedeGestionar={true} />
          </div>
        )}
      </div>
    </main>
  );
};

export const PANTALLAS_FOR_01: RegistroPantallas = {
  formacion: () => <FormacionGestion />,
  mi_formacion: () => <MiFormacion />,
};
