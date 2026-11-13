"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { obtenerContextoRolesCapa } from "@/lib/capa";
import {
  BASES_LEGITIMACION,
  CANALES,
  consultarConsentimientos,
  crearColectivo,
  editarColectivo,
  listarColectivos,
  registrarConsentimiento,
  ROLES_ESCRITURA,
  ROLES_LECTURA,
  type Colectivo,
  type RegistrosDeColectivo,
} from "@/lib/rat/consentimientos";
import { useRoadmapStore } from "@/store/useRoadmapStore";

/**
 * Pestaña «Titulares» de una ficha del RAT (RAT-07): colectivos y registro agregado de consentimientos.
 * Solo cantidades por fecha y canal; ningún campo identifica a una persona.
 */

const CONSENTIMIENTO = "CONSENTIMIENTO";
const ETIQUETA_BASE = Object.fromEntries(BASES_LEGITIMACION.map((b) => [b.valor, b.etiqueta]));
const ETIQUETA_CANAL = Object.fromEntries(CANALES.map((c) => [c.valor, c.etiqueta]));
const CAMPO = "w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-2";
const BOTON =
  "rounded-md bg-[var(--ui-primario)] px-3 py-1.5 font-semibold text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] disabled:opacity-50";

function mensajeDe(error: unknown): string {
  return error instanceof Error ? error.message : "No pudimos guardar los cambios. Inténtalo de nuevo.";
}

interface Props {
  ratId: string;
  nombre: string;
}

export default function Consentimientos({ ratId, nombre }: Props) {
  const sesion = useRoadmapStore((s) => s.session);
  const [roles, setRoles] = useState<string[]>(sesion.role ? [sesion.role] : []);
  const [uid, setUid] = useState(sesion.userId);
  const [colectivos, setColectivos] = useState<Colectivo[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editando, setEditando] = useState<string | null>(null);
  const [formColectivo, setFormColectivo] = useState(false);
  const [nombreColectivo, setNombreColectivo] = useState("");
  const [base, setBase] = useState(CONSENTIMIENTO);
  const [versionColectivo, setVersionColectivo] = useState("");

  const [seleccionado, setSeleccionado] = useState<Colectivo | null>(null);
  const [datos, setDatos] = useState<RegistrosDeColectivo | null>(null);
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [fecha, setFecha] = useState("");
  const [canal, setCanal] = useState("web");
  const [cantidad, setCantidad] = useState("");
  const [versionTexto, setVersionTexto] = useState("");
  const [errorCantidad, setErrorCantidad] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);

  const escribe = ROLES_ESCRITURA.some((r) => roles.includes(r));
  const rolActual = (rs: string[] = roles) => ROLES_LECTURA.find((r) => rs.includes(r)) ?? sesion.role;
  const rolEscritura = ROLES_ESCRITURA.find((r) => roles.includes(r)) ?? sesion.role;

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    let rolesActuales: string[] = sesion.role ? [sesion.role] : [];
    let usuario = sesion.userId;
    try {
      const contexto = await obtenerContextoRolesCapa();
      rolesActuales = contexto.roles;
      usuario = contexto.user_id || usuario;
      setRoles(rolesActuales);
      setUid(usuario);
    } catch {
      // Sin /organizacion/me/roles se conserva el rol de la sesión local.
    }
    try {
      setColectivos(await listarColectivos(ratId, rolActual(rolesActuales), usuario));
    } catch (e) {
      setError(mensajeDe(e));
    } finally {
      setCargando(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ratId, sesion.role, sesion.userId]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const cargarRegistros = useCallback(
    async (colectivo: Colectivo, d: string, h: string) => {
      try {
        setDatos(await consultarConsentimientos(colectivo.id, rolActual(), uid, d || undefined, h || undefined));
        setError(null);
      } catch (e) {
        setError(mensajeDe(e));
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [roles, uid],
  );

  function abrirColectivo(c: Colectivo) {
    setSeleccionado(c);
    setDatos(null);
    setAviso(null);
    void cargarRegistros(c, desde, hasta);
  }

  function nuevoColectivo() {
    setEditando(null);
    setNombreColectivo("");
    setBase(CONSENTIMIENTO);
    setVersionColectivo("");
    setFormColectivo(true);
  }

  function editar(c: Colectivo) {
    setEditando(c.id);
    setNombreColectivo(c.nombre);
    setBase(c.base_legitimacion);
    setVersionColectivo(c.texto_version ?? "");
    setFormColectivo(true);
  }

  async function guardarColectivo(e: React.FormEvent) {
    e.preventDefault();
    setGuardando(true);
    setError(null);
    const entrada = {
      nombre: nombreColectivo.trim(),
      base_legitimacion: base,
      texto_version: base === CONSENTIMIENTO && versionColectivo.trim() ? versionColectivo.trim() : null,
    };
    try {
      if (editando) await editarColectivo(editando, entrada, rolEscritura, uid);
      else await crearColectivo(ratId, entrada, rolEscritura, uid);
      setFormColectivo(false);
      await cargar();
    } catch (err) {
      setError(mensajeDe(err));
    } finally {
      setGuardando(false);
    }
  }

  async function registrar(e: React.FormEvent) {
    e.preventDefault();
    if (!seleccionado) return;
    const n = Number(cantidad);
    if (!Number.isInteger(n) || n <= 0) {
      setErrorCantidad("Escribe una cantidad mayor que cero.");
      return;
    }
    setErrorCantidad(null);
    setGuardando(true);
    setError(null);
    try {
      await registrarConsentimiento(
        seleccionado.id,
        { fecha, canal, cantidad: n, texto_version: versionTexto.trim() || null },
        rolEscritura,
        uid,
      );
      setCantidad("");
      setAviso("Registro guardado. Total actualizado.");
      await cargarRegistros(seleccionado, desde, hasta);
    } catch (err) {
      setError(mensajeDe(err));
    } finally {
      setGuardando(false);
    }
  }

  function cambiarRango(d: string, h: string) {
    setDesde(d);
    setHasta(h);
    if (seleccionado) void cargarRegistros(seleccionado, d, h);
  }

  const totalTexto = datos
    ? desde || hasta
      ? `Total del ${desde || "inicio"} al ${hasta || "hoy"}: ${datos.total}`
      : `Total: ${datos.total}`
    : "";

  return (
    <section aria-label={`Titulares de ${nombre}`} className="space-y-4 text-xs">
      <p role="note" className="rounded-lg border border-[var(--ui-borde)] p-3">
        Aquí solo se registran cantidades por fecha y canal. No se guardan datos de los titulares.
      </p>

      {error && (
        <p role="alert" className="rounded-lg border border-[var(--status-danger)] p-3 text-[var(--status-danger)]">
          {error}
        </p>
      )}
      {cargando && (
        <p className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> Cargando los colectivos…
        </p>
      )}

      {!cargando && colectivos.length === 0 && (
        <p className="text-[var(--ui-texto-suave)]">Este tratamiento aún no tiene colectivos.</p>
      )}

      {colectivos.length > 0 && (
        <ul className="space-y-2">
          {colectivos.map((c) => (
            <li key={c.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--ui-borde)] p-3">
              <span>
                <strong>{c.nombre}</strong> · {ETIQUETA_BASE[c.base_legitimacion] ?? c.base_legitimacion}
                {c.texto_version ? ` · texto ${c.texto_version}` : ""}
              </span>
              <span className="flex gap-2">
                <button type="button" onClick={() => abrirColectivo(c)} className="underline">
                  Ver registros de {c.nombre}
                </button>
                {escribe && (
                  <button type="button" onClick={() => editar(c)} className="underline">
                    Editar {c.nombre}
                  </button>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}

      {escribe && !formColectivo && (
        <button type="button" onClick={nuevoColectivo} className={BOTON}>
          Nuevo colectivo
        </button>
      )}

      {escribe && formColectivo && (
        <form onSubmit={guardarColectivo} aria-label="Colectivo" className="space-y-2 rounded-lg border border-[var(--ui-borde)] p-3">
          <label className="block space-y-1">
            <span className="font-medium">Nombre del colectivo</span>
            <input required maxLength={120} value={nombreColectivo} onChange={(e) => setNombreColectivo(e.target.value)} aria-describedby="ayuda-colectivo" className={CAMPO} />
            <span id="ayuda-colectivo" className="text-[var(--ui-texto-suave)]">Por ejemplo, socios, empleados o proveedores.</span>
          </label>
          <label className="block space-y-1">
            <span className="font-medium">Base de legitimación</span>
            <select value={base} onChange={(e) => setBase(e.target.value)} className={CAMPO}>
              {BASES_LEGITIMACION.map((b) => (
                <option key={b.valor} value={b.valor}>{b.etiqueta}</option>
              ))}
            </select>
          </label>
          {base === CONSENTIMIENTO && (
            <label className="block space-y-1">
              <span className="font-medium">Versión del texto de consentimiento</span>
              <input maxLength={16} value={versionColectivo} onChange={(e) => setVersionColectivo(e.target.value)} className={CAMPO} />
            </label>
          )}
          <div className="flex gap-2">
            <button type="submit" disabled={guardando} className={BOTON}>Guardar colectivo</button>
            <button type="button" onClick={() => setFormColectivo(false)} className="underline">Cancelar</button>
          </div>
        </form>
      )}

      {seleccionado && (
        <div className="space-y-3">
          {escribe && (
            <form onSubmit={registrar} aria-label="Registro de consentimientos" className="grid gap-2 rounded-lg border border-[var(--ui-borde)] p-3 sm:grid-cols-2">
              <label className="block space-y-1">
                <span className="font-medium">Fecha</span>
                <input type="date" required value={fecha} onChange={(e) => setFecha(e.target.value)} className={CAMPO} />
              </label>
              <label className="block space-y-1">
                <span className="font-medium">Canal</span>
                <select value={canal} onChange={(e) => setCanal(e.target.value)} className={CAMPO}>
                  {CANALES.map((c) => (
                    <option key={c.valor} value={c.valor}>{c.etiqueta}</option>
                  ))}
                </select>
              </label>
              <label className="block space-y-1">
                <span className="font-medium">Cantidad</span>
                <input inputMode="numeric" value={cantidad} onChange={(e) => setCantidad(e.target.value)} aria-invalid={errorCantidad ? true : undefined} className={CAMPO} />
                {errorCantidad && <span role="alert" className="text-[var(--status-danger)]">{errorCantidad}</span>}
              </label>
              <label className="block space-y-1">
                <span className="font-medium">Versión del texto</span>
                <input maxLength={16} value={versionTexto} onChange={(e) => setVersionTexto(e.target.value)} className={CAMPO} />
              </label>
              <div className="sm:col-span-2">
                <button type="submit" disabled={guardando} className={BOTON}>Registrar</button>
              </div>
            </form>
          )}
          {aviso && <p role="status">{aviso}</p>}

          <div className="flex flex-wrap gap-3">
            <label className="space-y-1">
              <span className="font-medium">Desde</span>
              <input type="date" value={desde} onChange={(e) => cambiarRango(e.target.value, hasta)} className={CAMPO} />
            </label>
            <label className="space-y-1">
              <span className="font-medium">Hasta</span>
              <input type="date" value={hasta} onChange={(e) => cambiarRango(desde, e.target.value)} className={CAMPO} />
            </label>
          </div>

          {datos && datos.registros.length === 0 && (
            <p className="text-[var(--ui-texto-suave)]">Aún no hay registros para este colectivo.</p>
          )}
          {datos && datos.registros.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <caption className="pb-2 text-left font-semibold">Registros de {seleccionado.nombre}</caption>
                <thead>
                  <tr>
                    <th scope="col" className="p-2">Fecha</th>
                    <th scope="col" className="p-2">Canal</th>
                    <th scope="col" className="p-2">Cantidad</th>
                    <th scope="col" className="p-2">Versión</th>
                  </tr>
                </thead>
                <tbody>
                  {datos.registros.map((r) => (
                    <tr key={r.id}>
                      <td className="p-2">{r.fecha}</td>
                      <td className="p-2">{ETIQUETA_CANAL[r.canal] ?? r.canal}</td>
                      <td className="p-2">{r.cantidad}</td>
                      <td className="p-2">{r.texto_version ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {datos && <p role="status">{totalTexto}</p>}
        </div>
      )}
    </section>
  );
}
