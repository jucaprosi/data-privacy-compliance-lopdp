// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa
// ¤¤frontend-architect
"use client";
/**
 * BIB-414 · «Capacidades editoriales»: quién del equipo de la plataforma puede editar, revisar y publicar plantillas
 * (UX/UI §2 y §6). Una fila por operador activo; la propia, desactivada; historial de concesiones y retiros.
 * Tres capacidades: Editor, Revisor técnico y Publicador.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { ETIQUETAS_CAPACIDAD } from "@/lib/biblioteca/capacidadesEditoriales";
import {
  CAPACIDADES_CONCEDIBLES, TEXTO_PROPIA, esPropia, listarEquipo, listarHistorial, textoDeError,
  type CapacidadConcedible, type EventoCapacidad, type MiembroEquipo,
} from "@/lib/plataforma/capacidadesEditoriales";
import DialogoCapacidad, { type Modo } from "./DialogoCapacidad";

const minuscula = (c: string) => (ETIQUETAS_CAPACIDAD[c as CapacidadConcedible] ?? c).toLowerCase();
const fecha = (iso: string) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString("es-EC", { dateStyle: "long" });
};

export default function CapacidadesEditoriales() {
  const [equipo, setEquipo] = useState<MiembroEquipo[] | null>(null);
  const [historial, setHistorial] = useState<EventoCapacidad[]>([]);
  const [error, setError] = useState("");
  const [errorHistorial, setErrorHistorial] = useState(false);
  const [dialogo, setDialogo] = useState<{ miembro: MiembroEquipo; modo: Modo } | null>(null);
  const abridor = useRef<HTMLElement | null>(null);

  const cargar = useCallback(async () => {
    let lista: MiembroEquipo[];
    try {
      lista = await listarEquipo();
      setEquipo(lista); setError("");
    } catch (e) { setError(textoDeError(e)); return; }
    // BIB-416 R1 y R2: el historial se pide por miembro y no tira al equipo si falla.
    try {
      const porMiembro = await Promise.all(lista.map((m) => listarHistorial(m.usuario_id)));
      setHistorial(porMiembro.flat().sort((a, b) => b.en.localeCompare(a.en))); setErrorHistorial(false);
    } catch { setHistorial([]); setErrorHistorial(true); }
  }, []);
  useEffect(() => { void cargar(); }, [cargar]);

  const nombreDe = (id: string | null) => equipo?.find((m) => m.usuario_id === id)?.nombre ?? id ?? "";
  const abrir = (miembro: MiembroEquipo, modo: Modo, e: React.MouseEvent<HTMLButtonElement>) => {
    abridor.current = e.currentTarget; setDialogo({ miembro, modo });
  };
  const cerrar = useCallback(() => {
    setDialogo(null);
    window.setTimeout(() => abridor.current?.focus(), 0);
  }, []);

  return <main aria-label="Capacidades editoriales" className="mx-auto max-w-6xl space-y-6 bg-[var(--ui-superficie)] p-6">
    <header>
      <h1 className="text-2xl font-bold">Capacidades editoriales</h1>
      <p>Quienes mantienen el catálogo de plantillas de la plataforma. Cada concesión y cada retiro quedan registrados con su motivo.</p>
    </header>
    {error && <p role="alert" className="rounded border border-[var(--ui-error-borde)] bg-[var(--ui-error-fondo)] p-3 text-[var(--ui-error-texto)]">{error}</p>}
    {!equipo && !error && <p role="status">Cargando…</p>}
    {equipo && <table className="w-full text-left max-md:block">
      <caption className="mb-2 text-left font-semibold">Operadores de la plataforma</caption>
      <thead className="max-md:sr-only"><tr>
        {["Nombre", "Correo", "Acceso", "Capacidades", "Acciones"].map((t) => <th key={t} scope="col" className="p-2">{t}</th>)}
      </tr></thead>
      <tbody className="max-md:block">
        {equipo.map((m) => {
          const propia = esPropia(m);
          const ayuda = `ayuda-propia-${m.usuario_id}`;
          const desactivada = propia ? { "aria-disabled": true as const, "aria-describedby": ayuda } : {};
          return <tr key={m.usuario_id} data-testid={`operador-${m.usuario_id}`}
            className="border-t border-[var(--ui-borde)] max-md:block max-md:rounded max-md:border max-md:p-3">
            <td className="p-2 max-md:block"><span className="md:hidden font-medium">Nombre: </span>{m.nombre}</td>
            <td className="p-2 max-md:block"><span className="md:hidden font-medium">Correo: </span>{m.email}</td>
            <td className="p-2 max-md:block"><span className="md:hidden font-medium">Acceso: </span>
              {m.ha_entrado ? "Vinculado a Google" : "Aún no ha entrado"}</td>
            <td className="p-2 max-md:block"><span className="md:hidden font-medium">Capacidades: </span>
              {m.capacidades.length === 0 ? "Sin capacidades" : <ul aria-label={`Capacidades de ${m.nombre}`} className="inline-flex flex-wrap gap-2">
                {m.capacidades.map((c) => <li key={c} className="rounded-full border border-[var(--ui-borde)] px-2 py-0.5 text-sm">
                  {ETIQUETAS_CAPACIDAD[c as CapacidadConcedible] ?? c}</li>)}
              </ul>}</td>
            <td className="p-2 max-md:block">
              <div className="flex flex-wrap gap-2">
                <button type="button" {...desactivada} onClick={(e) => { if (!propia) abrir(m, { tipo: "conceder" }, e); }}
                  className="rounded border p-2 aria-disabled:opacity-60">Conceder capacidad</button>
                {m.capacidades.filter((c): c is CapacidadConcedible => (CAPACIDADES_CONCEDIBLES as readonly string[]).includes(c)).map((c) =>
                  <button key={c} type="button" {...desactivada} aria-label={`Retirar ${minuscula(c)} a ${m.nombre}`}
                    onClick={(e) => { if (!propia) abrir(m, { tipo: "retirar", capacidad: c }, e); }}
                    className="rounded border border-[var(--ui-peligro-texto)] p-2 text-[var(--ui-peligro-texto)] aria-disabled:opacity-60">Retirar {ETIQUETAS_CAPACIDAD[c]}</button>)}
              </div>
              {propia && <p id={ayuda} className="mt-1 text-sm text-[var(--ui-texto-suave)]">{TEXTO_PROPIA}</p>}
            </td>
          </tr>;
        })}
      </tbody>
    </table>}
    <section aria-labelledby="titulo-historial-capacidades">
      <h2 id="titulo-historial-capacidades" className="text-xl font-semibold">Historial de concesiones</h2>
      {errorHistorial && <p role="alert" className="mt-2 rounded border border-[var(--ui-error-borde)] bg-[var(--ui-error-fondo)] p-3 text-[var(--ui-error-texto)]">No se pudo cargar el historial. Inténtalo de nuevo.</p>}
      {historial.length > 0 && <ol className="mt-2 grid gap-3">
        {historial.map((h) => <li key={h.id} className="rounded border border-[var(--ui-borde)] p-3">
          <p>{fecha(h.en)}</p>
          <p>{nombreDe(h.por)} {h.accion === "concedida" ? "concedió" : "retiró"} {minuscula(h.capacidad)} a {nombreDe(h.usuario_id)}</p>
          {h.motivo && <p className="text-[var(--ui-texto-suave)]">{h.motivo}</p>}
        </li>)}
      </ol>}
    </section>
    {dialogo && <DialogoCapacidad miembro={dialogo.miembro} modo={dialogo.modo} onCerrar={cerrar} onHecho={() => void cargar()} />}
  </main>;
}
