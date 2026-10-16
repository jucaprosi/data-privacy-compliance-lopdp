"use client";

import React, { useEffect, useId, useState } from "react";
import { AlertCircle, CheckCircle2, Loader2, Lock, RefreshCw } from "lucide-react";

import { useRoadmapStore } from "@/store/useRoadmapStore";
import { ApiError } from "@/types/roadmap";
import {
  CONTROLES,
  PLAZO_MAX_MESES,
  PLAZO_MIN_MESES,
  aVariables,
  formularioInicial,
  validar,
  type ErroresPlaneacion,
  type FormularioPlaneacion,
} from "./validacion";

/** Mensajes que cambian con el tiempo: la espera de la generación va de 20 a 90 s. */
const FASES_PROGRESO: ReadonlyArray<{ desdeSegundos: number; mensaje: string }> = [
  { desdeSegundos: 0, mensaje: "Preparando el análisis de tus variables de planeación…" },
  { desdeSegundos: 8, mensaje: "Generando las olas y las tareas de la hoja de ruta. Puede tardar hasta 90 segundos." },
  { desdeSegundos: 40, mensaje: "Validando que cada tarea cumpla la estructura y los controles exigidos…" },
  { desdeSegundos: 70, mensaje: "Sigue en curso. Estamos terminando; no cierres esta pantalla." },
];

export function mensajeDeProgreso(segundos: number): string {
  let actual = FASES_PROGRESO[0].mensaje;
  for (const fase of FASES_PROGRESO) {
    if (segundos >= fase.desdeSegundos) actual = fase.mensaje;
  }
  return actual;
}

interface ErrorGeneracion {
  mensaje: string;
  codigo?: string;
  accion?: string | null;
}

export interface PlaneacionFormProps {
  /** Se invoca con el identificador de la hoja de ruta cuando la generación termina. */
  onGenerado?: (roadmapId: string) => void;
}

const CAMPO =
  "w-full rounded-lg bg-[#0a0a0c] border border-[#26262b] px-3 py-2 text-sm text-zinc-100 " +
  "placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-[#3892f3] disabled:opacity-60";
const ETIQUETA = "block text-xs font-semibold text-zinc-300 mb-1";
const AYUDA = "text-[11px] text-zinc-500 mt-1";
const MENSAJE_ERROR = "text-[11px] text-[#ff6b86] mt-1";

export function PlaneacionForm({ onGenerado }: PlaneacionFormProps) {
  const idBase = useId();
  const rol = useRoadmapStore((s) => s.session.role);
  const generando = useRoadmapStore((s) => s.isGenerating);
  const generarRoadmap = useRoadmapStore((s) => s.generateRoadmap);

  const [form, setForm] = useState<FormularioPlaneacion>(formularioInicial);
  const [errores, setErrores] = useState<ErroresPlaneacion>({});
  const [errorGeneracion, setErrorGeneracion] = useState<ErrorGeneracion | null>(null);
  const [roadmapId, setRoadmapId] = useState<string | null>(null);
  const [segundos, setSegundos] = useState(0);

  const puedeGenerar = rol === "implementador";

  useEffect(() => {
    if (!generando) {
      setSegundos(0);
      return;
    }
    const inicio = Date.now();
    const temporizador = window.setInterval(() => {
      setSegundos(Math.floor((Date.now() - inicio) / 1000));
    }, 1000);
    return () => window.clearInterval(temporizador);
  }, [generando]);

  const id = (campo: string) => `${idBase}-${campo}`;

  function actualizar<K extends keyof FormularioPlaneacion>(campo: K, valor: FormularioPlaneacion[K]) {
    setForm((previo) => ({ ...previo, [campo]: valor }));
    if (errores[campo]) setErrores((previo) => ({ ...previo, [campo]: undefined }));
  }

  async function generar() {
    setErrorGeneracion(null);
    setRoadmapId(null);
    const encontrados = validar(form);
    setErrores(encontrados);
    if (Object.keys(encontrados).length > 0) return;

    try {
      const creado = await generarRoadmap(aVariables(form));
      setRoadmapId(creado);
      onGenerado?.(creado);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorGeneracion({ mensaje: err.message, codigo: err.code, accion: err.action_required });
      } else {
        setErrorGeneracion({ mensaje: "No se pudo completar la generación. Inténtalo de nuevo." });
      }
    }
  }

  function alEnviar(evento: React.FormEvent) {
    evento.preventDefault();
    if (!puedeGenerar || generando) return;
    void generar();
  }

  const bloqueado = !puedeGenerar || generando;

  return (
    <form
      onSubmit={alEnviar}
      noValidate
      aria-label="Variables de planeación"
      className="bg-[#141417] border border-[#26262b] rounded-xl p-5 space-y-5 text-zinc-200"
    >
      <header>
        <h2 className="text-sm font-bold uppercase tracking-wider text-white">Variables de planeación</h2>
        <p className="text-[11px] text-zinc-400 mt-0.5">
          Con estas variables se genera la hoja de ruta de adecuación. Los campos con asterisco son obligatorios.
        </p>
      </header>

      {!puedeGenerar && (
        <div
          role="note"
          className="flex items-start gap-2.5 p-3 rounded-lg bg-[#ffb300]/10 border border-[#ffb300]/40 text-xs"
        >
          <Lock className="w-4 h-4 shrink-0 mt-0.5 text-[#ffb300]" aria-hidden="true" />
          <p>
            Tu rol actual es <strong>{rol}</strong>. Solo el rol <strong>implementador</strong> puede generar la hoja de
            ruta; aquí puedes consultar las variables en modo de solo lectura.
          </p>
        </div>
      )}

      <fieldset disabled={bloqueado} className="space-y-5 min-w-0 border-0 p-0 m-0">
        <legend className="sr-only">Variables de la hoja de ruta</legend>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label htmlFor={id("plazo")} className={ETIQUETA}>
              Plazo en meses *
            </label>
            <input
              id={id("plazo")}
              type="number"
              inputMode="numeric"
              min={PLAZO_MIN_MESES}
              max={PLAZO_MAX_MESES}
              value={form.plazo_meses}
              onChange={(e) => actualizar("plazo_meses", e.target.value)}
              aria-invalid={Boolean(errores.plazo_meses)}
              aria-describedby={errores.plazo_meses ? id("plazo-error") : id("plazo-ayuda")}
              className={CAMPO}
            />
            {errores.plazo_meses ? (
              <p id={id("plazo-error")} role="alert" className={MENSAJE_ERROR}>
                {errores.plazo_meses}
              </p>
            ) : (
              <p id={id("plazo-ayuda")} className={AYUDA}>
                Entre {PLAZO_MIN_MESES} y {PLAZO_MAX_MESES} meses.
              </p>
            )}
          </div>

          <div>
            <label htmlFor={id("presupuesto")} className={ETIQUETA}>
              Presupuesto *
            </label>
            <input
              id={id("presupuesto")}
              type="number"
              inputMode="decimal"
              min={0}
              step="any"
              value={form.presupuesto}
              onChange={(e) => actualizar("presupuesto", e.target.value)}
              aria-invalid={Boolean(errores.presupuesto)}
              aria-describedby={errores.presupuesto ? id("presupuesto-error") : undefined}
              className={CAMPO}
            />
            {errores.presupuesto && (
              <p id={id("presupuesto-error")} role="alert" className={MENSAJE_ERROR}>
                {errores.presupuesto}
              </p>
            )}
          </div>

          <div>
            <label htmlFor={id("moneda")} className={ETIQUETA}>
              Moneda *
            </label>
            <input
              id={id("moneda")}
              type="text"
              maxLength={3}
              value={form.moneda}
              onChange={(e) => actualizar("moneda", e.target.value.toUpperCase())}
              aria-invalid={Boolean(errores.moneda)}
              aria-describedby={errores.moneda ? id("moneda-error") : id("moneda-ayuda")}
              className={CAMPO}
            />
            {errores.moneda ? (
              <p id={id("moneda-error")} role="alert" className={MENSAJE_ERROR}>
                {errores.moneda}
              </p>
            ) : (
              <p id={id("moneda-ayuda")} className={AYUDA}>
                Código de tres letras.
              </p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor={id("equipo")} className={ETIQUETA}>
              Equipo *
            </label>
            <textarea
              id={id("equipo")}
              rows={4}
              value={form.equipo}
              onChange={(e) => actualizar("equipo", e.target.value)}
              aria-invalid={Boolean(errores.equipo)}
              aria-describedby={errores.equipo ? id("equipo-error") : id("equipo-ayuda")}
              className={CAMPO}
            />
            {errores.equipo ? (
              <p id={id("equipo-error")} role="alert" className={MENSAJE_ERROR}>
                {errores.equipo}
              </p>
            ) : (
              <p id={id("equipo-ayuda")} className={AYUDA}>
                Un miembro o rol por línea.
              </p>
            )}
          </div>

          <div className="space-y-4">
            <div>
              <label htmlFor={id("dpo")} className={ETIQUETA}>
                Delegado de protección de datos *
              </label>
              <input
                id={id("dpo")}
                type="text"
                value={form.dpo}
                onChange={(e) => actualizar("dpo", e.target.value)}
                aria-invalid={Boolean(errores.dpo)}
                aria-describedby={errores.dpo ? id("dpo-error") : undefined}
                className={CAMPO}
              />
              {errores.dpo && (
                <p id={id("dpo-error")} role="alert" className={MENSAJE_ERROR}>
                  {errores.dpo}
                </p>
              )}
            </div>
            <div>
              <label htmlFor={id("idioma")} className={ETIQUETA}>
                Idioma del plan
              </label>
              <select
                id={id("idioma")}
                value={form.idioma}
                onChange={(e) => actualizar("idioma", e.target.value as "ES" | "EN")}
                className={CAMPO}
              >
                <option value="ES">Español</option>
                <option value="EN">Inglés</option>
              </select>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor={id("sistemas")} className={ETIQUETA}>
              Sistemas y proveedores
            </label>
            <textarea
              id={id("sistemas")}
              rows={3}
              value={form.sistemas_proveedores}
              onChange={(e) => actualizar("sistemas_proveedores", e.target.value)}
              className={CAMPO}
            />
          </div>
          <div>
            <label htmlFor={id("contratos")} className={ETIQUETA}>
              Contratos relevantes
            </label>
            <textarea
              id={id("contratos")}
              rows={3}
              value={form.contratos_relevantes}
              onChange={(e) => actualizar("contratos_relevantes", e.target.value)}
              className={CAMPO}
            />
          </div>
          <div>
            <label htmlFor={id("prioridades")} className={ETIQUETA}>
              Prioridades del negocio
            </label>
            <textarea
              id={id("prioridades")}
              rows={3}
              value={form.prioridades_negocio}
              onChange={(e) => actualizar("prioridades_negocio", e.target.value)}
              aria-describedby={id("prioridades-ayuda")}
              className={CAMPO}
            />
            <p id={id("prioridades-ayuda")} className={AYUDA}>
              Una por línea.
            </p>
          </div>
          <div>
            <label htmlFor={id("restricciones")} className={ETIQUETA}>
              Restricciones locales
            </label>
            <textarea
              id={id("restricciones")}
              rows={3}
              value={form.restricciones_locales}
              onChange={(e) => actualizar("restricciones_locales", e.target.value)}
              className={CAMPO}
            />
          </div>
        </div>

        <details className="rounded-lg border border-[#26262b] bg-[#0a0a0c] p-3">
          <summary className="cursor-pointer text-xs font-semibold text-zinc-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#3892f3] rounded">
            Evidencia que ya existe por control (opcional)
          </summary>
          <fieldset className="mt-3 border-0 p-0 m-0">
            <legend className="sr-only">Controles con evidencia disponible</legend>
            <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
              {CONTROLES.map((control) => (
                <label key={control} className="flex items-center gap-1.5 text-xs text-zinc-300">
                  <input
                    type="checkbox"
                    checked={Boolean(form.evidencia_por_control[control])}
                    onChange={(e) =>
                      actualizar("evidencia_por_control", {
                        ...form.evidencia_por_control,
                        [control]: e.target.checked,
                      })
                    }
                    className="accent-[#3892f3]"
                  />
                  {control}
                </label>
              ))}
            </div>
          </fieldset>
        </details>
      </fieldset>

      {generando && (
        <div
          role="status"
          aria-live="polite"
          className="flex items-start gap-2.5 p-3 rounded-lg bg-[#3892f3]/10 border border-[#3892f3]/40 text-xs"
        >
          <Loader2 className="w-4 h-4 shrink-0 mt-0.5 text-[#3892f3] animate-spin" aria-hidden="true" />
          <div className="space-y-1">
            <p data-testid="progreso-mensaje">{mensajeDeProgreso(segundos)}</p>
            <p className="text-zinc-400">Tiempo transcurrido: {segundos} s</p>
          </div>
        </div>
      )}

      {errorGeneracion && (
        <div role="alert" className="flex items-start gap-2.5 p-3 rounded-lg bg-[#ff1744]/10 border border-[#ff1744]/40 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[#ff1744]" aria-hidden="true" />
          <div className="space-y-1">
            <p data-testid="error-mensaje">{errorGeneracion.mensaje}</p>
            {errorGeneracion.codigo && (
              <p className="text-zinc-400">
                Código: <span data-testid="error-codigo">{errorGeneracion.codigo}</span>
              </p>
            )}
            {errorGeneracion.accion && (
              <p className="text-zinc-400">
                Acción requerida: <span data-testid="error-accion">{errorGeneracion.accion}</span>
              </p>
            )}
          </div>
        </div>
      )}

      {roadmapId && !generando && !errorGeneracion && (
        <div
          role="status"
          className="flex items-start gap-2.5 p-3 rounded-lg bg-[#00c853]/10 border border-[#00c853]/40 text-xs"
        >
          <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-[#00c853]" aria-hidden="true" />
          <p>
            La hoja de ruta se generó correctamente. Identificador: <span data-testid="roadmap-id">{roadmapId}</span>
          </p>
        </div>
      )}

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={bloqueado}
          className="inline-flex items-center gap-2 rounded-lg bg-[#3892f3] px-4 py-2 text-sm font-semibold text-white hover:bg-[#2f7fd6] focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-[#141417] focus-visible:ring-[#3892f3] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {generando ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : null}
          {generando ? "Generando…" : errorGeneracion ? "Reintentar generación" : "Generar hoja de ruta"}
          {!generando && errorGeneracion ? <RefreshCw className="w-4 h-4" aria-hidden="true" /> : null}
        </button>
      </div>
    </form>
  );
}

export default PlaneacionForm;
