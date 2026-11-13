"use client";
// ¤riesgos-eipd
// ¤¤frontend-architect
// Riesgos y auditoría › Evaluaciones de impacto (MTGE-03): lista por tratamiento y asistente.
import React, { useCallback, useEffect, useState } from "react";
import AsistenteEipd from "./AsistenteEipd";
import {
  catalogosEipd, crearEipd, listarEipd, listarTratamientos, mensajeDeError, misRolesEipd, puedeCerrar,
  puedeEditar, type Catalogos, type Eipd, type Tratamiento,
} from "@/lib/eipd/cliente";

const estadoDe = (e: Eipd) => (e.cerrada_en ? "Cerrada" : `Borrador · paso ${Math.min(e.paso_actual, 8)} de 8`);

export default function EvaluacionesImpacto() {
  const [roles, setRoles] = useState<string[]>([]);
  const [lista, setLista] = useState<Eipd[]>([]);
  const [tratamientos, setTratamientos] = useState<Tratamiento[]>([]);
  const [catalogos, setCatalogos] = useState<Catalogos | null>(null);
  const [abierta, setAbierta] = useState<Eipd | null>(null);
  const [dialogo, setDialogo] = useState(false);
  const [elegido, setElegido] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const [r, l, t, c] = await Promise.all([misRolesEipd(), listarEipd(), listarTratamientos(), catalogosEipd()]);
      setRoles(r); setLista(l); setTratamientos(t); setCatalogos(c); setError(null);
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => { void cargar(); }, [cargar]);

  const nombre = (id: string) => tratamientos.find((t) => t.id === id)?.nombre ?? "Tratamiento";
  const editor = puedeEditar(roles);

  const crear = async () => {
    if (!elegido) return;
    try {
      const nueva = await crearEipd(elegido);
      setDialogo(false); setElegido(""); setLista([nueva, ...lista]); setAbierta(nueva);
    } catch (e) {
      setError(mensajeDeError(e));
    }
  };

  if (abierta && catalogos) {
    return (
      <AsistenteEipd eipd={abierta} catalogos={catalogos} nombreTratamiento={nombre(abierta.tratamiento_id)}
        soloLectura={!editor} puedeCerrar={puedeCerrar(roles)}
        alCambiar={(e) => { setAbierta(e); setLista((l) => l.map((x) => (x.id === e.id ? e : x))); }}
        alVolver={() => { setAbierta(null); void cargar(); }} />
    );
  }

  return (
    <section className="flex min-w-0 flex-col gap-4" aria-labelledby="eipd-titulo">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 id="eipd-titulo" className="text-xl font-semibold">Evaluaciones de impacto</h1>
        {editor ? (
          <button type="button" onClick={() => setDialogo(true)}
            className="rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-sm text-[var(--ui-primario-texto)]">
            Nueva evaluación
          </button>
        ) : null}
      </div>
      {!editor && !cargando ? (
        <p className="text-sm text-[var(--ui-texto-suave)]">Puedes revisar la evaluación; la completa el equipo responsable.</p>
      ) : null}
      {error ? <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{error}</p> : null}
      {dialogo ? (
        <div role="dialog" aria-modal="true" aria-labelledby="eipd-dialogo"
          className="flex flex-col gap-2 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4">
          <h2 id="eipd-dialogo" className="font-semibold">Tratamiento a evaluar</h2>
          <select aria-labelledby="eipd-dialogo" value={elegido} onChange={(e) => setElegido(e.target.value)}
            className="w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-2 text-sm">
            <option value="">Elige un tratamiento</option>
            {tratamientos.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
          </select>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setDialogo(false)}
              className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm">Cancelar</button>
            <button type="button" onClick={() => void crear()} disabled={!elegido}
              className="rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-sm text-[var(--ui-primario-texto)] disabled:opacity-50">
              Crear
            </button>
          </div>
        </div>
      ) : null}
      {cargando ? <p className="text-sm">Cargando…</p> : lista.length === 0 ? (
        <p className="text-sm text-[var(--ui-texto-suave)]">Aún no hay evaluaciones de impacto.</p>
      ) : (
        <ul className="flex flex-col divide-y divide-[var(--ui-borde)] rounded-lg border border-[var(--ui-borde)]" data-testid="eipd-lista">
          {lista.map((e) => (
            <li key={e.id} className="flex flex-wrap items-center justify-between gap-2 p-3 text-sm">
              <span className="min-w-0 break-words font-medium">{nombre(e.tratamiento_id)}</span>
              <span className="flex items-center gap-2">
                <span className={`rounded px-2 py-0.5 ${e.cerrada_en ? "badge-render-success" : "badge-render-warning"}`}>{estadoDe(e)}</span>
                <button type="button" onClick={() => setAbierta(e)} className="underline">Abrir</button>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
