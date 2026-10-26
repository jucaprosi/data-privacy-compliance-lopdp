"use client";

import React, { useEffect, useState } from "react";
import { ClipboardList, Loader2 } from "lucide-react";

import { requestJson } from "@/lib/roadmap/cliente";

/**
 * Plantilla sectorial del RAT (RAT-02).
 *
 * Solo aparece si el servidor ofrece una plantilla para el sector de la organización. El
 * coordinador elige qué actividades aplican y las carga; nada se carga sin confirmación. Bases
 * legales y plazos llegan al RAT como «sugerido, validar».
 */

interface ActividadPlantilla {
  codigo: string;
  nombre: string;
  finalidad: string;
  actor_sugerido: string;
}

interface Plantilla {
  sector: string;
  version: string;
  fuente: string;
  actividades: ActividadPlantilla[];
}

interface ResultadoCarga {
  creadas: string[];
  omitidas: string[];
}

export default function PlantillaSectorial({ onCargada }: { onCargada?: () => void }) {
  const [plantilla, setPlantilla] = useState<Plantilla | null>(null);
  const [abierta, setAbierta] = useState(false);
  const [elegidas, setElegidas] = useState<Set<string>>(new Set());
  const [cargando, setCargando] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    requestJson<{ plantillas: Plantilla[] }>("/rat/plantillas")
      .then(({ plantillas }) => setPlantilla(plantillas[0] ?? null))
      .catch(() => setPlantilla(null));
  }, []);

  if (!plantilla) return null;

  const alternar = (codigo: string, marcada: boolean) => {
    const copia = new Set(elegidas);
    if (marcada) copia.add(codigo);
    else copia.delete(codigo);
    setElegidas(copia);
  };

  async function cargar() {
    if (!plantilla) return;
    setCargando(true);
    setError(null);
    setMensaje(null);
    try {
      const r = await requestJson<ResultadoCarga>(`/rat/plantillas/${plantilla.sector}/aplicar`, {
        method: "POST",
        body: JSON.stringify({ codigos: [...elegidas] }),
      });
      setMensaje(
        `Se cargaron ${r.creadas.length} actividades` +
          (r.omitidas.length ? `; ${r.omitidas.length} ya estaban cargadas.` : ".") +
          " Revise y valide sus bases legales y plazos.",
      );
      setElegidas(new Set());
      onCargada?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cargar la plantilla.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <section
      aria-label="Plantilla de salud"
      className="rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 space-y-3 text-xs"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="flex items-center gap-2">
          <ClipboardList className="w-4 h-4" aria-hidden="true" />
          <span>
            Hay una plantilla de {plantilla.sector} con {plantilla.actividades.length} actividades típicas
            <span className="text-[var(--ui-texto-suave)]"> ({plantilla.fuente}, {plantilla.version})</span>.
          </span>
        </p>
        <button
          type="button"
          onClick={() => setAbierta((v) => !v)}
          aria-expanded={abierta}
          className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 font-semibold hover:bg-[var(--ui-boton-hover)]"
        >
          {abierta ? "Ocultar" : "Cargar plantilla de salud"}
        </button>
      </div>

      {abierta && (
        <div className="space-y-3">
          <p className="text-[var(--ui-texto-suave)]">
            Marque las actividades que realiza su organización. Las bases legales y los plazos de conservación son
            sugerencias: valídelos antes de darlos por definitivos.
          </p>
          <fieldset className="space-y-1.5">
            <legend className="sr-only">Actividades de la plantilla</legend>
            {plantilla.actividades.map((a) => (
              <label key={a.codigo} className="flex items-start gap-2">
                <input
                  type="checkbox"
                  className="mt-0.5"
                  checked={elegidas.has(a.codigo)}
                  onChange={(e) => alternar(a.codigo, e.target.checked)}
                />
                <span>
                  <strong>{a.nombre}</strong>
                  <span className="text-[var(--ui-texto-suave)]"> · {a.finalidad} · actor sugerido: {a.actor_sugerido}</span>
                </span>
              </label>
            ))}
          </fieldset>
          <button
            type="button"
            onClick={cargar}
            disabled={cargando || elegidas.size === 0}
            className="inline-flex items-center gap-1.5 rounded-md bg-[var(--ui-primario)] px-3 py-1.5 font-semibold text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] disabled:opacity-50"
          >
            {cargando && <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />}
            Cargar {elegidas.size} actividades en el RAT
          </button>
        </div>
      )}

      {mensaje && <p role="status">{mensaje}</p>}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
