// ¤dlp-muestreo
/**
 * Pantalla de DLP-01: descubrimiento de datos personales en una muestra. Solo DLP-01 edita este archivo.
 * La muestra vive solo en el formulario; del servidor llegan tipos y conteos. Los errores se muestran con
 * textos fijos por código: nunca el texto del servidor, que podría traer valores de la muestra.
 */
"use client";

import React, { useCallback, useEffect, useId, useRef, useState } from "react";
import { fetchAutenticado, leerOrganizacionActiva } from "@/lib/auth";
import { getActividadesRAT } from "@/lib/api";
import { obtenerContextoRolesCapa } from "@/lib/capa";
import type { ActividadRAT } from "@/types";
import type { RegistroPantallas } from "./base";

const API = "/api/v1/dlp-discovery";
export const MAXIMO_FILAS = 1000;

export const NOMBRE_TIPO: Record<string, string> = {
  EC_CEDULA_MOD10: "Cédulas de identidad",
  EC_RUC: "Números de RUC",
  EMAIL: "Correos electrónicos",
  PHONE: "Números de teléfono",
  SALUD: "Posibles datos de salud",
};

const TEXTO_EXCEDE = `La muestra supera el máximo de ${MAXIMO_FILAS} filas. Reduce la muestra e inténtalo de nuevo.`;
const NOTA_SALUD = "Revisa la muestra antes de vincularlo: la detección de datos de salud puede dar falsos positivos.";
const TEXTO_ERROR = "No pudimos escanear la muestra. Inténtalo de nuevo.";
const TEXTO_ERROR_VINCULO = "No pudimos vincular las categorías. Inténtalo de nuevo.";

/** Escanean coordinador, administración e implementación; el DPO solo consulta. */
const ROLES = ["coordinador", "admin_organizacion", "implementador", "dpo"];

interface Escaneo {
  id: string;
  fuente_nombre: string;
  infotypes_detectados: Record<string, number>;
  actividad_rat_id: string | null;
  creado_por: string | null;
  creado_en: string | null;
}

function rolDe(roles: string[]): string | null {
  return ROLES.find((r) => roles.includes(r)) ?? null;
}

async function llamar(ruta: string, rol: string | null, init: RequestInit = {}): Promise<Response> {
  return fetchAutenticado(`${API}${ruta}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(rol ? { "X-Role": rol } : {}) },
  });
}

async function codigoDeError(res: Response): Promise<string | null> {
  const cuerpo = await res.json().catch(() => null);
  const codigo = cuerpo?.detail?.codigo;
  return typeof codigo === "string" ? codigo : null;
}

export function filasDe(texto: string): string[] {
  return texto.split(/\r?\n/).filter((f) => f.trim() !== "");
}

function nombreTipo(codigo: string): string {
  return NOMBRE_TIPO[codigo] ?? "Otro tipo de dato";
}

function TablaTipos({ tipos }: { tipos: [string, number][] }) {
  return (
    <>
      <table className="hidden w-full text-sm sm:table">
        <caption className="mb-2 text-left font-medium">Tipos de datos encontrados</caption>
        <thead>
          <tr className="border-b text-left">
            <th scope="col" className="py-2">Tipo</th>
            <th scope="col" className="py-2 text-right">Cantidad</th>
          </tr>
        </thead>
        <tbody>
          {tipos.map(([codigo, cantidad]) => (
            <tr key={codigo} className="border-b">
              <td className="py-2">{nombreTipo(codigo)}</td>
              <td className="py-2 text-right tabular-nums">{cantidad}</td>
            </tr>
          )).flatMap((fila, i) =>
            tipos[i][0] === "SALUD"
              ? [fila, <tr key="SALUD-nota"><td colSpan={2} className="pb-2 text-xs text-gray-600">{NOTA_SALUD}</td></tr>]
              : [fila]
          )}
        </tbody>
      </table>
      <ul className="space-y-2 sm:hidden" aria-label="Tipos de datos encontrados">
        {tipos.map(([codigo, cantidad]) => (
          <li key={codigo} className="flex flex-wrap justify-between rounded border p-3 text-sm">
            <span>{nombreTipo(codigo)}</span>
            <span className="tabular-nums">{cantidad}</span>
            {codigo === "SALUD" && <span className="basis-full text-xs text-gray-600">{NOTA_SALUD}</span>}
          </li>
        ))}
      </ul>
    </>
  );
}

export default function DescubrimientoDatos() {
  const ids = { fuente: useId(), muestra: useId(), archivo: useId(), actividad: useId() };
  const [rol, setRol] = useState<string | null>(() => rolDe(leerOrganizacionActiva()?.roles ?? []));
  const [fuente, setFuente] = useState("");
  const [texto, setTexto] = useState("");
  const [escaneando, setEscaneando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<Escaneo | null>(null);
  const [historial, setHistorial] = useState<Escaneo[]>([]);
  const [actividades, setActividades] = useState<ActividadRAT[]>([]);
  const [actividadId, setActividadId] = useState("");
  const [elegidos, setElegidos] = useState<string[]>([]);
  const [aviso, setAviso] = useState("");
  const [muestraBorrada, setMuestraBorrada] = useState(false);
  const tituloResultado = useRef<HTMLHeadingElement>(null);

  const puedeEscanear = rol !== null && rol !== "dpo";
  const puedeVincular = rol === "coordinador";
  const filas = filasDe(texto);

  const cargarHistorial = useCallback(async () => {
    const res = await llamar("/escaneos", rol).catch(() => null);
    if (res?.ok) setHistorial(((await res.json()) as { escaneos: Escaneo[] }).escaneos);
  }, [rol]);

  useEffect(() => {
    // Sin /organizacion/me/roles se conserva el rol de la organización activa.
    obtenerContextoRolesCapa()
      .then((c) => setRol(rolDe(c.roles)))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    void cargarHistorial();
    if (puedeVincular) getActividadesRAT().then(setActividades).catch(() => setActividades([]));
  }, [cargarHistorial, puedeVincular]);

  useEffect(() => {
    if (resultado) tituloResultado.current?.focus();
  }, [resultado]);

  async function leerArchivo(e: React.ChangeEvent<HTMLInputElement>) {
    const archivo = e.target.files?.[0];
    if (archivo) setTexto(await archivo.text());
    e.target.value = "";
  }

  async function escanear(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setAviso("");
    setMuestraBorrada(false);
    if (filas.length > MAXIMO_FILAS) {
      setError(TEXTO_EXCEDE);
      return;
    }
    setEscaneando(true);
    try {
      const res = await llamar("/escanear-muestra", rol, {
        method: "POST",
        body: JSON.stringify({ fuente_nombre: fuente.trim(), limite_muestra: MAXIMO_FILAS, filas }),
      });
      if (!res.ok) {
        setError((await codigoDeError(res)) === "DLP_MUESTRA_EXCEDE_LIMITE" ? TEXTO_EXCEDE : TEXTO_ERROR);
        return;
      }
      const escaneo = (await res.json()) as Escaneo;
      setTexto(""); // la muestra no se conserva tampoco en la pantalla
      setMuestraBorrada(true);
      setElegidos([]);
      setResultado(escaneo);
      void cargarHistorial();
    } catch {
      setError(TEXTO_ERROR);
    } finally {
      setEscaneando(false);
    }
  }

  async function vincular(e: React.FormEvent) {
    e.preventDefault();
    if (!resultado || !actividadId || elegidos.length === 0) return;
    setError(null);
    const res = await llamar(`/escaneos/${resultado.id}/vincular-rat`, rol, {
      method: "POST",
      body: JSON.stringify({ actividad_rat_id: actividadId, infotypes: elegidos }),
    }).catch(() => null);
    if (!res?.ok) {
      setError(TEXTO_ERROR_VINCULO);
      return;
    }
    const nombre = actividades.find((a) => a.id === actividadId)?.nombre ?? "la actividad";
    setAviso(`Categorías vinculadas a ${nombre}.`);
    void cargarHistorial();
  }

  const tipos = resultado
    ? (Object.entries(resultado.infotypes_detectados).filter(([, n]) => n > 0) as [string, number][])
    : [];

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-6">
      <header>
        <h1 className="text-2xl font-semibold">Descubrimiento de datos</h1>
        <p className="text-sm text-gray-600">Detecta tipos de datos personales en una muestra</p>
      </header>

      <p role="note" className="rounded border border-blue-200 bg-blue-50 p-3 text-sm">
        Revisamos la muestra solo para contar los tipos de datos personales que contiene. No guardamos la muestra
        ni los valores encontrados; solo los conteos.
      </p>

      {error && (
        <p role="alert" className="rounded border border-red-200 bg-red-50 p-3 text-sm">
          {error}
        </p>
      )}

      {puedeEscanear && (
        <form onSubmit={escanear} className="space-y-4 rounded border p-4" aria-busy={escaneando}>
          <h2 className="text-lg font-medium">Escanear muestra</h2>
          <div>
            <label htmlFor={ids.fuente} className="block text-sm font-medium">Nombre de la fuente</label>
            <input
              id={ids.fuente}
              required
              maxLength={160}
              value={fuente}
              onChange={(e) => setFuente(e.target.value)}
              aria-describedby={`${ids.fuente}-ayuda`}
              className="mt-1 w-full rounded border p-2"
            />
            <p id={`${ids.fuente}-ayuda`} className="text-xs text-gray-600">
              Por ejemplo, la base de socios o una hoja de cálculo.
            </p>
          </div>
          <div>
            <label htmlFor={ids.muestra} className="block text-sm font-medium">Muestra</label>
            <textarea
              id={ids.muestra}
              required
              rows={8}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              aria-describedby={`${ids.muestra}-ayuda`}
              className="mt-1 w-full rounded border p-2 font-mono text-sm"
            />
            <div id={`${ids.muestra}-ayuda`} className="flex flex-wrap justify-between gap-2 text-xs text-gray-600">
              <span>Máximo {MAXIMO_FILAS} filas por muestra. Usa solo las filas necesarias.</span>
              <span>{filas.length} de {MAXIMO_FILAS} filas</span>
            </div>
            <label htmlFor={ids.archivo} className="mt-2 block text-sm">O carga un archivo de texto</label>
            <input id={ids.archivo} type="file" accept=".csv,.txt,text/plain,text/csv" onChange={leerArchivo} />
          </div>
          <button
            type="submit"
            disabled={escaneando || filas.length === 0 || fuente.trim() === ""}
            className="rounded bg-blue-700 px-4 py-2 text-white disabled:opacity-50"
          >
            Escanear muestra
          </button>
          {escaneando && <p role="status">Escaneando la muestra…</p>}
          {muestraBorrada && <p role="status" className="text-sm">La muestra se borró de esta pantalla.</p>}
        </form>
      )}

      {resultado && (
        <section className="space-y-4 rounded border p-4" aria-labelledby="dlp01-resultado">
          <h2 id="dlp01-resultado" ref={tituloResultado} tabIndex={-1} className="text-lg font-medium">
            Resultado del escaneo
          </h2>
          <div role="status" aria-live="polite">
            {tipos.length === 0 ? (
              <p>No encontramos datos personales en esta muestra.</p>
            ) : (
              <TablaTipos tipos={tipos} />
            )}
          </div>
          {tipos.length > 0 && (
            <p className="text-xs text-gray-600">
              Es una ayuda para revisar tu inventario. Confirma cada categoría antes de vincularla.
            </p>
          )}

          {puedeVincular && tipos.length > 0 && (
            <form onSubmit={vincular} className="space-y-3 border-t pt-4">
              <div>
                <label htmlFor={ids.actividad} className="block text-sm font-medium">Actividad de tratamiento</label>
                <select
                  id={ids.actividad}
                  value={actividadId}
                  onChange={(e) => setActividadId(e.target.value)}
                  className="mt-1 w-full rounded border p-2"
                >
                  <option value="">Selecciona una actividad</option>
                  {actividades.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.codigo} · {a.nombre}
                    </option>
                  ))}
                </select>
              </div>
              <fieldset className="space-y-1">
                <legend className="text-sm font-medium">Categorías</legend>
                {tipos.map(([codigo]) => (
                  <label key={codigo} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={elegidos.includes(codigo)}
                      onChange={(e) =>
                        setElegidos((prev) => (e.target.checked ? [...prev, codigo] : prev.filter((c) => c !== codigo)))
                      }
                    />
                    Vincular {nombreTipo(codigo).toLowerCase()}
                  </label>
                ))}
              </fieldset>
              <button
                type="submit"
                disabled={!actividadId || elegidos.length === 0}
                className="rounded bg-blue-700 px-4 py-2 text-white disabled:opacity-50"
              >
                Vincular al registro de actividades
              </button>
              {aviso && <p role="status">{aviso}</p>}
            </form>
          )}
        </section>
      )}

      <section className="space-y-2" aria-labelledby="dlp01-historial">
        <h2 id="dlp01-historial" className="text-lg font-medium">Escaneos anteriores</h2>
        {historial.length === 0 ? (
          <p className="text-sm text-gray-600">Aún no hay escaneos.</p>
        ) : (
          <ul className="divide-y rounded border">
            {historial.map((h) => (
              <li key={h.id} className="flex flex-col gap-1 p-3 text-sm sm:flex-row sm:justify-between">
                <span>{h.creado_en ? new Date(h.creado_en).toLocaleString("es-EC") : "—"}</span>
                <span className="font-medium">{h.fuente_nombre}</span>
                <span>{h.creado_por ?? "—"}</span>
                <span>
                  {Object.values(h.infotypes_detectados).filter((n) => n > 0).length} tipos encontrados
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

export const PANTALLAS_DLP_01: RegistroPantallas = {
  descubrimiento_datos: () => <DescubrimientoDatos />,
};
