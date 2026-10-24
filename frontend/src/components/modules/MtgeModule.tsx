"use client";

import React, { useState } from "react";
import { AlertTriangle, Calculator, CheckCircle, Loader2, Scale } from "lucide-react";

import { evaluarMTGE, type EntradaMTGE } from "@/lib/api";
import type { ResultadoMTGE } from "@/types";

/**
 * Calculadora del Modelo Técnico de Gran Escala (Res. SPDP-SPD-2026-0005-R).
 *
 * El cálculo lo hace el servidor (MTGE-01): esta pantalla solo recoge las seis variables del art. 7
 * y los supuestos del art. 14, y muestra el resultado con su desglose. Si el servidor falla se
 * muestra el error; nunca se calcula aquí.
 */

const CATEGORIAS: { valor: EntradaMTGE["categorias_datos"]; etiqueta: string }[] = [
  { valor: "BASICAS", etiqueta: "Solo datos básicos (0,5)" },
  { valor: "UNA_ESPECIAL", etiqueta: "Una categoría especial (2)" },
  { valor: "VARIAS_ESPECIALES_VULNERABLES_O_PENALES", etiqueta: "Varias especiales, grupos vulnerables o datos penales (3)" },
];
const FRECUENCIAS: { valor: EntradaMTGE["frecuencia"]; etiqueta: string }[] = [
  { valor: "PUNTUAL", etiqueta: "Puntual (0,5)" },
  { valor: "PERIODICA", etiqueta: "Periódica o recurrente (1)" },
  { valor: "CONTINUA", etiqueta: "Continua o en tiempo real (2)" },
];
const PERMANENCIAS: { valor: EntradaMTGE["permanencia"]; etiqueta: string }[] = [
  { valor: "OCASIONAL", etiqueta: "Ocasional (0,5)" },
  { valor: "TEMPORAL", etiqueta: "Temporal, menos de 3 años (1)" },
  { valor: "PROLONGADA", etiqueta: "Prolongada, desde 3 años (2)" },
];
const ALCANCES: { valor: EntradaMTGE["alcance"]; etiqueta: string }[] = [
  { valor: "LOCAL", etiqueta: "Local: una provincia, cantón o ciudad (1)" },
  { valor: "NACIONAL", etiqueta: "Nacional: más de una (2)" },
  { valor: "GLOBAL_O_TRANSFRONTERIZO", etiqueta: "Global o transfronterizo (3)" },
];
const SUPUESTOS: { valor: string; etiqueta: string }[] = [
  { valor: "SALUD_O_CATEGORIAS_ESPECIALES", etiqueta: "14.1 Salud, historias clínicas u otras categorías especiales" },
  { valor: "PERFILAMIENTO_CON_EFECTOS_JURIDICOS", etiqueta: "14.2 Perfilamiento automatizado con efectos jurídicos" },
  { valor: "VIDEOVIGILANCIA_EN_ACCESO_PUBLICO", etiqueta: "14.3 Videovigilancia sistemática en zonas de acceso público" },
  { valor: "BIOMETRICOS_O_GEOLOCALIZACION", etiqueta: "14.4 Datos biométricos o geolocalización" },
  { valor: "CREDITO_SOLVENCIA_O_RIESGO_ECONOMICO", etiqueta: "14.5 Crédito, solvencia o riesgo económico" },
  { valor: "NINAS_NINOS_Y_ADOLESCENTES", etiqueta: "14.5 Niñas, niños y adolescentes (sistemático)" },
  { valor: "TRANSFERENCIAS_SISTEMATICAS", etiqueta: "14.6 Transferencias sistemáticas" },
  { valor: "MENSAJERIA_O_COURIER", etiqueta: "14.7 Mensajería acelerada, expresa o courier" },
];
const NOMBRE_VARIABLE: Record<string, string> = {
  titulares: "Titulares en 12 meses (art. 8.1)",
  volumen: "Tipos de datos por titular (art. 8.2)",
  categorias: "Categorías de datos (art. 8.3)",
  frecuencia: "Frecuencia (art. 8.4)",
  permanencia: "Permanencia (art. 8.5)",
  geografia: "Alcance geográfico (art. 8.6)",
};

const CAMPO =
  "w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[var(--ui-primario)]";
const ETIQUETA = "block text-[11px] font-semibold text-[var(--ui-texto-suave)] mb-1";

export default function MtgeModule() {
  const [entrada, setEntrada] = useState<EntradaMTGE>({
    actividad_rat_id: "calculadora",
    titulares_12_meses: 800,
    tipos_datos_por_titular: 25,
    categorias_datos: "UNA_ESPECIAL",
    frecuencia: "PERIODICA",
    permanencia: "PROLONGADA",
    alcance: "LOCAL",
    supuestos_directos: [],
  });
  const [resultado, setResultado] = useState<ResultadoMTGE | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [calculando, setCalculando] = useState(false);

  const cambiar = (cambios: Partial<EntradaMTGE>) => {
    setEntrada((actual) => ({ ...actual, ...cambios }));
    setResultado(null);
  };

  const alternarSupuesto = (valor: string, marcado: boolean) =>
    cambiar({
      supuestos_directos: marcado
        ? [...entrada.supuestos_directos, valor]
        : entrada.supuestos_directos.filter((s) => s !== valor),
    });

  async function calcular(evento: React.FormEvent) {
    evento.preventDefault();
    setCalculando(true);
    setError(null);
    try {
      setResultado(await evaluarMTGE(entrada));
    } catch (err) {
      setResultado(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setCalculando(false);
    }
  }

  return (
    <section aria-label="Calculadora de gran escala" className="space-y-6">
      <header className="pb-4 border-b border-[var(--ui-borde)]">
        <h2 className="text-xl font-bold flex items-center">
          <Scale className="w-5 h-5 mr-2" aria-hidden="true" /> Tratamiento a gran escala (MTGE)
        </h2>
        <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
          Resolución SPDP-SPD-2026-0005-R. El cálculo es por tratamiento: gran escala si cae en un supuesto del
          art. 14 o si la suma de las seis variables llega a 6 puntos (art. 10).
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <form
          onSubmit={calcular}
          aria-label="Variables del tratamiento"
          className="lg:col-span-2 rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-6 space-y-5"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="mtge-titulares" className={ETIQUETA}>Titulares únicos en 12 meses</label>
              <input
                id="mtge-titulares"
                type="number"
                min={0}
                required
                className={CAMPO}
                value={entrada.titulares_12_meses}
                onChange={(e) => cambiar({ titulares_12_meses: Number(e.target.value) })}
              />
            </div>
            <div>
              <label htmlFor="mtge-tipos" className={ETIQUETA}>Tipos de datos por titular</label>
              <input
                id="mtge-tipos"
                type="number"
                min={1}
                required
                className={CAMPO}
                value={entrada.tipos_datos_por_titular}
                onChange={(e) => cambiar({ tipos_datos_por_titular: Number(e.target.value) })}
              />
            </div>
            <Selector id="mtge-categorias" etiqueta="Categorías de datos" opciones={CATEGORIAS}
              valor={entrada.categorias_datos} onChange={(v) => cambiar({ categorias_datos: v })} />
            <Selector id="mtge-frecuencia" etiqueta="Frecuencia" opciones={FRECUENCIAS}
              valor={entrada.frecuencia} onChange={(v) => cambiar({ frecuencia: v })} />
            <Selector id="mtge-permanencia" etiqueta="Permanencia" opciones={PERMANENCIAS}
              valor={entrada.permanencia} onChange={(v) => cambiar({ permanencia: v })} />
            <Selector id="mtge-alcance" etiqueta="Alcance geográfico" opciones={ALCANCES}
              valor={entrada.alcance} onChange={(v) => cambiar({ alcance: v })} />
          </div>

          <fieldset className="space-y-2">
            <legend className={ETIQUETA}>Calificación directa (art. 14): marque los que apliquen</legend>
            {SUPUESTOS.map((s) => (
              <label key={s.valor} className="flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={entrada.supuestos_directos.includes(s.valor)}
                  onChange={(e) => alternarSupuesto(s.valor, e.target.checked)}
                />
                {s.etiqueta}
              </label>
            ))}
          </fieldset>

          <button
            type="submit"
            disabled={calculando}
            className="inline-flex items-center gap-1.5 rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-xs font-semibold text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] disabled:opacity-50"
          >
            {calculando ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Calculator className="w-4 h-4" aria-hidden="true" />}
            Calcular
          </button>
        </form>

        <div role="region" aria-label="Resultado del cálculo" className="rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-6 space-y-4">
          {error && (
            <p role="alert" className="text-xs">
              No se pudo calcular en el servidor: {error}
            </p>
          )}
          {!error && !resultado && (
            <p className="text-xs text-[var(--ui-texto-suave)]">Complete las variables y pulse «Calcular».</p>
          )}
          {resultado && (
            <>
              <p data-testid="mtge-veredicto" className="text-sm font-bold flex items-center gap-1.5">
                {resultado.es_gran_escala ? (
                  <><AlertTriangle className="w-4 h-4" aria-hidden="true" /> Gran escala</>
                ) : (
                  <><CheckCircle className="w-4 h-4" aria-hidden="true" /> No es gran escala</>
                )}
              </p>
              <p data-testid="mtge-puntaje" className="text-xs">
                Puntaje: <strong>{resultado.puntaje_mtge.toLocaleString("es-EC")}</strong> de 6 necesarios
              </p>
              <table className="w-full text-xs">
                <caption className="sr-only">Desglose por variable</caption>
                <tbody>
                  {Object.entries(resultado.desglose).map(([clave, puntos]) => (
                    <tr key={clave} className="border-b border-[var(--ui-borde)]">
                      <th scope="row" className="py-1 pr-2 text-left font-normal text-[var(--ui-texto-suave)]">{NOMBRE_VARIABLE[clave] ?? clave}</th>
                      <td className="py-1 text-right">{puntos.toLocaleString("es-EC")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs">{resultado.rationale}</p>
              {resultado.es_gran_escala && (
                <ul className="text-xs list-disc pl-4 space-y-0.5" aria-label="Efectos del art. 12">
                  <li>Evaluación de impacto previa (art. 12.1)</li>
                  <li>DPO Obligatorio (Art. 48): delegado de protección de datos (LOPDP art. 48 y art. 12.2 de la resolución)</li>
                  <li>Incluir el tratamiento en el RAT (art. 12.3)</li>
                  <li>Medidas reforzadas de responsabilidad proactiva, seguridad y supervisión (art. 12.4)</li>
                </ul>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  );
}

function Selector<T extends string>(props: {
  id: string;
  etiqueta: string;
  opciones: { valor: T; etiqueta: string }[];
  valor: T;
  onChange: (valor: T) => void;
}) {
  return (
    <div>
      <label htmlFor={props.id} className={ETIQUETA}>{props.etiqueta}</label>
      <select id={props.id} className={CAMPO} value={props.valor} onChange={(e) => props.onChange(e.target.value as T)}>
        {props.opciones.map((o) => (
          <option key={o.valor} value={o.valor}>{o.etiqueta}</option>
        ))}
      </select>
    </div>
  );
}
