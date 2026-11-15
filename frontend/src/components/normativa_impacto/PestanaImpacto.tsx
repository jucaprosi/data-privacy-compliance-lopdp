"use client";
/**
 * Pestaña «Impacto» del detalle de una resolución (NORM-03): lista de elementos afectados con su cita, aviso de IA y,
 * para el DPO, «Aceptar» y «Rechazar» con nota obligatoria. Se monta dentro de la pantalla de NORM-02.
 */
import { useCallback, useEffect, useState } from "react";

import {
  decidirImpacto, ErrorImpacto, listarImpactos, pedirAnalisis, type AnalisisImpacto,
} from "./cliente";
import { AVISO_IA, ESTADO_IMPACTO, MENSAJES, TIPO_ELEMENTO } from "./etiquetas";

function mensaje(e: unknown, porDefecto: string): string {
  return MENSAJES[(e as ErrorImpacto).codigo ?? ""] ?? porDefecto;
}

const BOTON = "rounded border border-[var(--ui-borde)] px-3 py-1 text-sm";

export default function PestanaImpacto({ resolucionId, esDpo, puedePedir }: {
  resolucionId: string; esDpo: boolean; puedePedir: boolean;
}) {
  const [analisis, setAnalisis] = useState<AnalisisImpacto[] | null>(null);
  const [fallo, setFallo] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [decidiendo, setDecidiendo] = useState<{ id: string; decision: "aceptar" | "rechazar" } | null>(null);
  const [nota, setNota] = useState("");
  const [errorNota, setErrorNota] = useState("");

  const cargar = useCallback(async () => {
    try { setAnalisis(await listarImpactos(resolucionId)); setFallo(""); }
    catch { setFallo("No pudimos cargar el análisis. Inténtalo de nuevo."); }
  }, [resolucionId]);

  useEffect(() => { void cargar(); }, [cargar]);

  const pedir = async () => {
    setOcupado(true); setFallo("");
    try { await pedirAnalisis(resolucionId); await cargar(); }
    catch (e) { setFallo(mensaje(e, "No pudimos generar el análisis.")); }
    finally { setOcupado(false); }
  };

  const abrirDecision = (id: string, decision: "aceptar" | "rechazar") => {
    setDecidiendo({ id, decision }); setNota(""); setErrorNota("");
  };

  const decidir = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!decidiendo) return;
    if (nota.trim().length < 10) { setErrorNota(MENSAJES.NORMATIVA_IMPACTO_NOTA_OBLIGATORIA); return; }
    try {
      await decidirImpacto(decidiendo.id, decidiendo.decision, nota);
      setDecidiendo(null); setNota(""); setErrorNota("");
      await cargar();
    } catch (err) {
      setErrorNota(mensaje(err, "No pudimos guardar la decisión."));
    }
  };

  return (
    <section role="tabpanel" aria-label="Impacto" className="flex flex-col gap-3">
      <p role="note" className="rounded border border-[var(--ui-borde)] p-2 text-sm">{AVISO_IA}</p>
      {puedePedir ? (
        <div>
          <button type="button" disabled={ocupado} onClick={pedir} className={BOTON}>
            {ocupado ? "Analizando…" : "Analizar impacto en mi organización"}
          </button>
        </div>
      ) : null}
      {fallo ? <p role="alert" className="text-sm">{fallo}</p> : null}
      {analisis && analisis.length === 0 ? <p className="text-sm">Aún no hay un análisis de esta norma.</p> : null}
      {(analisis ?? []).map((a) => (
        <article key={a.id} aria-label={`Análisis del ${a.creada_en.slice(0, 10)}`}
          className="flex flex-col gap-2 rounded border border-[var(--ui-borde)] p-3">
          <header className="flex items-center justify-between gap-2">
            <span className={`text-sm ${ESTADO_IMPACTO[a.estado].clase}`}>{ESTADO_IMPACTO[a.estado].texto}</span>
            <span className="text-xs opacity-70">{a.creada_en.slice(0, 10)}</span>
          </header>
          {a.sin_base_normativa ? (
            <p className="text-sm">La norma no da base para proponer cambios en tu organización.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {a.propuesta.map((el) => (
                <li key={`${el.tipo}:${el.referencia_id}`} className="text-sm">
                  <strong>{TIPO_ELEMENTO[el.tipo]}</strong> · {el.referencia_id}
                  <p>{el.motivo}</p>
                  <p className="opacity-80">Cita: {el.articulos_citados.join(", ")}</p>
                </li>
              ))}
            </ul>
          )}
          {a.estado !== "propuesta" && a.nota ? <p className="text-sm">Nota del DPO: {a.nota}</p> : null}
          {a.estado === "propuesta" && esDpo ? (
            <div className="flex gap-2">
              <button type="button" onClick={() => abrirDecision(a.id, "aceptar")} className={BOTON}>Aceptar</button>
              <button type="button" onClick={() => abrirDecision(a.id, "rechazar")} className={BOTON}>Rechazar</button>
            </div>
          ) : null}
          {decidiendo?.id === a.id ? (
            <form onSubmit={decidir} className="flex flex-col gap-2"
              aria-label={decidiendo.decision === "aceptar" ? "Aceptar la propuesta" : "Rechazar la propuesta"}>
              <label className="text-sm">Nota de la decisión
                <textarea value={nota} onChange={(e) => setNota(e.target.value)} rows={3}
                  aria-invalid={errorNota ? true : undefined}
                  className="mt-1 w-full rounded border border-[var(--ui-borde)] p-2" />
              </label>
              {errorNota ? <p role="alert" className="text-sm">{errorNota}</p> : null}
              <div className="flex gap-2">
                <button type="submit" className={BOTON}>
                  Confirmar {decidiendo.decision === "aceptar" ? "aceptación" : "rechazo"}
                </button>
                <button type="button" onClick={() => setDecidiendo(null)} className={BOTON}>Cancelar</button>
              </div>
            </form>
          ) : null}
        </article>
      ))}
    </section>
  );
}
