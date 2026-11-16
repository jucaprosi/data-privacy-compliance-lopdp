"use client";
// ¤riesgos-eipd ¤asistente
// ¤¤frontend-architect
// Asistente de ocho pasos de la evaluación de impacto (MTGE-03) sobre el patrón FE-23.
import React, { useMemo, useState } from "react";
import { Asistente, type PasoAsistente } from "@/components/asistente";
import {
  DECISIONES, NIVELES, cerrarEipd, cierreBloqueado, guardarPaso, informeEipd, mensajeDeError,
  type Catalogos, type Decision, type Eipd, type NivelRiesgo,
} from "@/lib/eipd/cliente";

interface Props {
  eipd: Eipd;
  catalogos: Catalogos;
  nombreTratamiento: string;
  soloLectura: boolean;
  puedeCerrar: boolean;
  alCambiar: (eipd: Eipd) => void;
  alVolver: () => void;
}

const falta = (que: string) => `Completa este paso antes de continuar: ${que}.`;
const campo = "w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-2 text-sm";

export default function AsistenteEipd({ eipd, catalogos, nombreTratamiento, soloLectura, puedeCerrar, alCambiar, alVolver }: Props) {
  const [obligatoria, setObligatoria] = useState(eipd.obligatoria);
  const [consulta, setConsulta] = useState(eipd.consulta_titulares ?? "");
  const [fases, setFases] = useState<string[]>(eipd.ciclo_vida?.fases ?? []);
  const [amenazas, setAmenazas] = useState<string[]>(eipd.ciclo_vida?.amenazas ?? []);
  const [necesidad, setNecesidad] = useState(eipd.necesidad ?? "");
  const [puntos, setPuntos] = useState<string[]>(eipd.puntos.map((p) => p.texto));
  const [nuevoPunto, setNuevoPunto] = useState("");
  const [inherente, setInherente] = useState<NivelRiesgo | null>(eipd.riesgo_inherente);
  const [residual, setResidual] = useState<NivelRiesgo | null>(eipd.riesgo_residual);
  const [decision, setDecision] = useState<Decision | null>(eipd.decision);
  const [justificacion, setJustificacion] = useState(eipd.decision_texto ?? "");
  const [error, setError] = useState<string | null>(null);
  const [huella, setHuella] = useState<string | null>(eipd.informe_sha256);
  const [cerrando, setCerrando] = useState(false);
  const cerrada = huella !== null;
  const bloqueado = soloLectura || cerrada;

  const alternar = (lista: string[], valor: string, fijar: (l: string[]) => void) =>
    fijar(lista.includes(valor) ? lista.filter((v) => v !== valor) : [...lista, valor]);

  const cuerpos: Record<string, () => Record<string, unknown>> = {
    p1: () => ({ obligatoria }),
    p2: () => ({ consulta_titulares: consulta.trim() }),
    p3: () => ({ fases, amenazas }),
    p4: () => ({ necesidad: necesidad.trim() }),
    p5: () => ({ puntos }),
    p6: () => ({ riesgo_inherente: inherente, riesgo_residual: residual }),
    p7: () => ({ decision, decision_texto: decision ? justificacion.trim() : null }),
  };

  const guardar = async (pasoId: string) => {
    if (bloqueado || !cuerpos[pasoId]) return;
    setError(null);
    try {
      alCambiar(await guardarPaso(eipd.id, Number(pasoId.slice(1)), cuerpos[pasoId]()));
    } catch (e) {
      setError(mensajeDeError(e));
      throw e;
    }
  };

  const cerrar = async () => {
    if (!puedeCerrar || cierreBloqueado(residual, decision) || cerrando) return;
    setCerrando(true);
    setError(null);
    try {
      setHuella((await cerrarEipd(eipd.id)).informe_sha256);
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setCerrando(false);
    }
  };

  const descargar = async () => {
    try {
      const informe = await informeEipd(eipd.id);
      const blob = new Blob([JSON.stringify(informe, null, 2)], { type: "application/json" });
      const enlace = document.createElement("a");
      enlace.href = URL.createObjectURL(blob);
      enlace.download = `evaluacion-impacto-${eipd.id}.json`;
      enlace.click();
      URL.revokeObjectURL(enlace.href);
    } catch (e) {
      setError(mensajeDeError(e));
    }
  };

  const bloqueoCierre = cierreBloqueado(residual, decision);
  const radioNivel = (nombre: string, valor: NivelRiesgo | null, fijar: (v: NivelRiesgo) => void) => (
    <fieldset className="flex flex-wrap gap-3" disabled={bloqueado}>
      <legend className="mb-1 text-sm font-medium">{nombre}</legend>
      {(Object.keys(NIVELES) as NivelRiesgo[]).map((n) => (
        <label key={n} className="flex items-center gap-1 text-sm">
          <input type="radio" name={nombre} checked={valor === n} onChange={() => fijar(n)} />
          {NIVELES[n]}
        </label>
      ))}
    </fieldset>
  );

  const pasos: PasoAsistente[] = useMemo(() => [
    {
      id: "p1", titulo: "Identificación y obligatoriedad", opcional: false, validar: () => null,
      contenido: (
        <div className="flex flex-col gap-2 text-sm">
          <p>Tratamiento: <strong>{nombreTratamiento}</strong></p>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={obligatoria} data-testid="eipd-obligatoria"
              disabled={bloqueado || eipd.obligatoria_por_ley}
              aria-describedby={eipd.obligatoria_por_ley ? "eipd-motivo" : undefined}
              onChange={(e) => setObligatoria(e.target.checked)} />
            La evaluación es obligatoria
          </label>
          {eipd.obligatoria_por_ley ? (
            <p id="eipd-motivo" className="text-[var(--ui-texto-suave)]">
              La ley exige esta evaluación para este tratamiento: {eipd.motivo_obligatoriedad}.
            </p>
          ) : null}
        </div>
      ),
    },
    {
      id: "p2", titulo: "Consulta a titulares", opcional: false,
      validar: () => (consulta.trim() ? null : falta("describe cómo se consultó a los titulares")),
      contenido: (
        <label className="flex flex-col gap-1 text-sm">Consulta realizada
          <textarea className={campo} rows={4} value={consulta} disabled={bloqueado}
            onChange={(e) => setConsulta(e.target.value)} />
        </label>
      ),
    },
    {
      id: "p3", titulo: "Ciclo de vida y amenazas", opcional: false,
      validar: () => (fases.length && amenazas.length ? null : falta("elige al menos una fase y una amenaza")),
      contenido: (
        <div className="grid gap-4 sm:grid-cols-2">
          {([["Fases del ciclo de vida", catalogos.fases, fases, setFases],
            ["Amenazas", catalogos.amenazas, amenazas, setAmenazas]] as const).map(([titulo, catalogo, lista, fijar]) => (
            <fieldset key={titulo} className="flex flex-col gap-1 text-sm" disabled={bloqueado}>
              <legend className="mb-1 font-medium">{titulo}</legend>
              {Object.entries(catalogo).map(([clave, etiqueta]) => (
                <label key={clave} className="flex items-center gap-2">
                  <input type="checkbox" checked={lista.includes(clave)}
                    onChange={() => alternar(lista, clave, fijar as (l: string[]) => void)} />
                  {etiqueta}
                </label>
              ))}
            </fieldset>
          ))}
        </div>
      ),
    },
    {
      id: "p4", titulo: "Necesidad y proporcionalidad", opcional: false,
      validar: () => (necesidad.trim() ? null : falta("explica la necesidad y la proporcionalidad")),
      contenido: (
        <label className="flex flex-col gap-1 text-sm">Análisis
          <textarea className={campo} rows={4} value={necesidad} disabled={bloqueado}
            onChange={(e) => setNecesidad(e.target.value)} />
        </label>
      ),
    },
    {
      id: "p5", titulo: "Puntos por corregir", opcional: false, validar: () => null,
      contenido: (
        <div className="flex flex-col gap-2 text-sm">
          <p className="text-[var(--ui-texto-suave)]">Cada punto se registra como un hallazgo del plan de acción.</p>
          <ul className="list-disc pl-5" data-testid="eipd-puntos">
            {puntos.map((p) => <li key={p} className="break-words">{p}</li>)}
          </ul>
          {!bloqueado ? (
            <div className="flex flex-wrap gap-2">
              <label className="flex min-w-0 flex-1 flex-col gap-1">Nuevo punto
                <input className={campo} value={nuevoPunto} onChange={(e) => setNuevoPunto(e.target.value)} />
              </label>
              <button type="button" className="self-end rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5"
                onClick={() => {
                  const t = nuevoPunto.trim();
                  if (t && !puntos.includes(t)) setPuntos([...puntos, t]);
                  setNuevoPunto("");
                }}>Añadir punto</button>
            </div>
          ) : null}
        </div>
      ),
    },
    {
      id: "p6", titulo: "Riesgo inherente y residual", opcional: false,
      validar: () => (inherente && residual ? null : falta("elige el riesgo inherente y el residual")),
      contenido: (
        <div className="flex flex-col gap-3">
          {radioNivel("Riesgo inherente", inherente, setInherente)}
          {radioNivel("Riesgo residual", residual, setResidual)}
        </div>
      ),
    },
    {
      id: "p7", titulo: "Decisión", opcional: false,
      validar: () => (decision && !justificacion.trim() ? falta("escribe la justificación") : null),
      contenido: (
        <div className="flex flex-col gap-3 text-sm">
          <p className="text-[var(--ui-texto-suave)]">
            La decisión es del responsable del tratamiento; la plataforma la registra con su justificación.
          </p>
          <div className="grid gap-2 sm:grid-cols-3" role="radiogroup" aria-label="Decisión">
            {(Object.keys(DECISIONES) as Decision[]).map((d) => (
              <button key={d} type="button" role="radio" aria-checked={decision === d} disabled={bloqueado}
                onClick={() => setDecision(decision === d ? null : d)}
                className={`rounded-lg border p-3 text-left ${decision === d
                  ? "border-[var(--ui-primario)] bg-[var(--ui-boton-hover)]" : "border-[var(--ui-borde)] bg-[var(--ui-boton)]"}`}>
                {DECISIONES[d]}
              </button>
            ))}
          </div>
          {decision ? (
            <label className="flex flex-col gap-1">Justificación
              <textarea className={campo} rows={3} value={justificacion} required disabled={bloqueado}
                onChange={(e) => setJustificacion(e.target.value)} />
            </label>
          ) : null}
        </div>
      ),
    },
    {
      id: "p8", titulo: "Informe final", opcional: false, validar: () => null,
      contenido: (
        <div className="flex flex-col gap-3 text-sm">
          {cerrada ? (
            <>
              <p><span className="badge-render-success rounded px-2 py-0.5">Cerrada</span></p>
              <p data-testid="eipd-huella">Huella de integridad: {huella!.slice(0, 8)}</p>
              <button type="button" onClick={() => void descargar()}
                aria-label={`Descargar el informe de la evaluación de ${nombreTratamiento}`}
                className="self-start rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-[var(--ui-primario-texto)]">
                Descargar el informe
              </button>
            </>
          ) : puedeCerrar && !soloLectura ? (
            <>
              <button type="button" onClick={() => void cerrar()} data-testid="eipd-cerrar"
                aria-disabled={bloqueoCierre || cerrando} aria-describedby={bloqueoCierre ? "eipd-bloqueo" : undefined}
                className={`self-start rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-[var(--ui-primario-texto)] ${bloqueoCierre ? "opacity-50" : ""}`}>
                Cerrar la evaluación
              </button>
              {bloqueoCierre ? (
                <p id="eipd-bloqueo" className="text-[var(--ui-texto-suave)]">
                  Con riesgo residual alto, elige una decisión antes de cerrar.
                </p>
              ) : null}
            </>
          ) : (
            <p className="text-[var(--ui-texto-suave)]">La cierra el equipo responsable.</p>
          )}
        </div>
      ),
    },
  // eslint-disable-next-line react-hooks/exhaustive-deps
  ], [obligatoria, consulta, fases, amenazas, necesidad, puntos, nuevoPunto, inherente, residual, decision,
      justificacion, huella, cerrando, bloqueado, catalogos, eipd, nombreTratamiento, puedeCerrar, soloLectura]);

  return (
    <div className="flex min-w-0 flex-col gap-3">
      <button type="button" onClick={alVolver} className="self-start text-sm underline">Volver a la lista</button>
      {soloLectura ? (
        <p className="text-sm text-[var(--ui-texto-suave)]">Puedes revisar la evaluación; la completa el equipo responsable.</p>
      ) : null}
      {error ? <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{error}</p> : null}
      <Asistente pasos={pasos} guardar={guardar} alTerminar={() => undefined}
        pasoInicial={Math.min(eipd.paso_actual, 8) - 1} />
    </div>
  );
}
