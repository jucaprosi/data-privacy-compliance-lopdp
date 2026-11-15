"use client";

/**
 * DER-01 · Ficha de una solicitud de titular: verificación de identidad y respuesta registrada como evidencia.
 *
 * La plataforma no envía nada al titular: «Registrar la respuesta» la deja como evidencia y la persona la
 * entrega por el medio que indicó el titular. Los textos son los cerrados por UX/UI (ficha DER-01).
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";

import {
  METODOS,
  cargarFicha,
  cargarModelos,
  descargarRespuesta,
  documentoDeLaRespuesta,
  errorDe,
  etiquetaDeVariable,
  etiquetasDeResultado,
  FalloRespuesta,
  huellaCorta,
  permisosDelUsuario,
  registrarRespuesta,
  verificarIdentidad,
  vistaPrevia,
  type FichaSolicitud,
  type MetodoIdentidad,
  type ModeloRespuesta,
  type PermisosDeRespuesta,
  type ResultadoRespuesta,
} from "@/lib/derechos/respuestas";

const RESULTADOS: ResultadoRespuesta[] = ["concedido", "parcial", "denegado"];

const fecha = (iso: string) =>
  new Date(iso).toLocaleDateString("es-EC", { day: "2-digit", month: "2-digit", year: "numeric" });

const etiquetaMetodo = (m: MetodoIdentidad | null) => METODOS.find((x) => x.valor === m)?.etiqueta ?? "";

const boton =
  "rounded border border-[var(--ui-borde)] px-3 py-1.5 text-xs font-medium  " +
  "hover:border-[var(--ui-primario)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--ui-primario)]";

export default function FichaRespuesta({ solicitudId, derecho }: { solicitudId: string; derecho: string }) {
  const [ficha, setFicha] = useState<FichaSolicitud | null>(null);
  const [permisos, setPermisos] = useState<PermisosDeRespuesta | null>(null);
  const [cargando, setCargando] = useState(true);
  const [falloCarga, setFalloCarga] = useState(false);
  const [metodo, setMetodo] = useState<MetodoIdentidad | null>(null);
  const [resultado, setResultado] = useState<ResultadoRespuesta>("concedido");
  const [modelos, setModelos] = useState<ModeloRespuesta[]>([]);
  const [modeloId, setModeloId] = useState("");
  const [valores, setValores] = useState<Record<string, string>>({});
  const [tocados, setTocados] = useState(false);
  const [confirmando, setConfirmando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exito, setExito] = useState(false);
  const [documentoId, setDocumentoId] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setFalloCarga(false);
    try {
      const [f, p] = await Promise.all([cargarFicha(solicitudId), permisosDelUsuario()]);
      setFicha(f);
      setPermisos(p);
    } catch {
      setFalloCarga(true);
    } finally {
      setCargando(false);
    }
  }, [solicitudId]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const identidadVerificada = ficha?.identidad_verificada_en != null;
  const respondida = ficha?.respondida_en != null;

  useEffect(() => {
    if (!identidadVerificada || respondida) return;
    let vigente = true;
    cargarModelos(derecho, resultado)
      .then((m) => {
        if (!vigente) return;
        setModelos(m);
        setModeloId(m[0]?.id ?? "");
        setValores({});
        setTocados(false);
      })
      .catch(() => vigente && setModelos([]));
    return () => {
      vigente = false;
    };
  }, [identidadVerificada, respondida, derecho, resultado]);

  useEffect(() => {
    if (!respondida || !ficha?.evidencia_respuesta_hash) return;
    void documentoDeLaRespuesta(ficha.evidencia_respuesta_hash).then(setDocumentoId);
  }, [respondida, ficha?.evidencia_respuesta_hash]);

  const modelo = modelos.find((m) => m.id === modeloId) ?? null;
  const previa = useMemo(() => (modelo ? vistaPrevia(modelo.texto, valores) : null), [modelo, valores]);
  const incompleta = !modelo || (previa?.faltan.length ?? 0) > 0;
  const etiquetas = etiquetasDeResultado(derecho);

  async function alVerificar() {
    if (!metodo) return;
    setError(null);
    try {
      setFicha(await verificarIdentidad(solicitudId, metodo));
    } catch (e) {
      setError(e instanceof FalloRespuesta ? e.detalle.mensaje : (await errorDe(new Response(null, { status: 500 }))).mensaje);
    }
  }

  async function alRegistrar() {
    if (!modelo) return;
    setError(null);
    setConfirmando(false);
    try {
      await registrarRespuesta(solicitudId, { modelo_id: modelo.id, variables: valores, resultado });
      setExito(true);
      await cargar();
    } catch (e) {
      const detalle = e instanceof FalloRespuesta ? e.detalle : null;
      setError(detalle?.mensaje ?? "No pudimos guardar los cambios. Inténtalo de nuevo.");
      if (detalle?.codigo === "SOLICITUD_RESPONDIDA") await cargar();
    }
  }

  if (cargando) {
    return (
      <p role="status" className="text-sm text-[var(--ui-texto-suave)]">
        Cargando la solicitud…
      </p>
    );
  }
  if (falloCarga || !ficha || !permisos) {
    return (
      <div className="space-y-2">
        <p role="alert" className="text-sm badge-render-danger">
          No pudimos cargar la solicitud. Inténtalo de nuevo.
        </p>
        <button type="button" className={boton} onClick={() => void cargar()}>
          Volver a cargar
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="ficha-respuesta">
      <section aria-labelledby="bloque-identidad" className="space-y-2">
        <h3 id="bloque-identidad" className="text-sm font-semibold ">
          Identidad
        </h3>
        {identidadVerificada ? (
          <p role="status" className="text-xs text-[var(--ui-texto-suave)]">
            {`Identidad verificada por ${ficha.identidad_verificada_por_nombre ?? "—"} el ${fecha(ficha.identidad_verificada_en as string)} · ${etiquetaMetodo(ficha.identidad_metodo)}.`}
          </p>
        ) : permisos.puedeVerificar ? (
          <>
            <p className="text-xs text-[var(--ui-texto-suave)]">
              Comprueba que quien pide es el titular o su representante antes de responder.
            </p>
            <div role="radiogroup" aria-label="Método de verificación" className="flex flex-wrap gap-4">
              {METODOS.map((m) => (
                <label key={m.valor} className="flex items-center gap-1.5 text-xs ">
                  <input
                    type="radio"
                    name="metodo-identidad"
                    checked={metodo === m.valor}
                    onChange={() => setMetodo(m.valor)}
                  />
                  {m.etiqueta}
                </label>
              ))}
            </div>
            {!metodo && <p className="text-xs text-[var(--ui-texto-suave)]">Elige cómo verificaste la identidad.</p>}
            <button
              type="button"
              className={boton}
              aria-label="Verificar la identidad del titular"
              aria-disabled={!metodo}
              onClick={() => metodo && void alVerificar()}
            >
              Verificar
            </button>
          </>
        ) : (
          <p className="text-xs text-[var(--ui-texto-suave)]">Verifica la identidad del titular para poder responder.</p>
        )}
      </section>

      <section aria-labelledby="bloque-respuesta" className="space-y-3">
        <h3 id="bloque-respuesta" className="text-sm font-semibold ">
          Respuesta
        </h3>
        {!identidadVerificada ? (
          <p className="text-xs text-[var(--ui-texto-suave)]">Verifica la identidad del titular para poder responder.</p>
        ) : respondida ? (
          <div className="space-y-1 text-xs ">
            <p>
              <span className="font-semibold">Respondida</span>
              {` el ${fecha(ficha.respondida_en as string)} · ${ficha.resultado ? etiquetas[ficha.resultado] : ""}`}
            </p>
            {ficha.evidencia_respuesta_hash && (
              <p className="text-[var(--ui-texto-suave)]">
                {`Huella de integridad: ${huellaCorta(ficha.evidencia_respuesta_hash)}`}
              </p>
            )}
            {documentoId && (
              <p className="flex gap-4">
                <a className="underline" href={`/api/v1/evidencias/documentos/${documentoId}/archivo`} target="_blank" rel="noreferrer">
                  Ver la respuesta registrada
                </a>
                <button type="button" className="underline" onClick={() => void descargarRespuesta(documentoId)}>
                  Descargar la respuesta
                </button>
              </p>
            )}
            {exito && (
              <p role="status">Respuesta registrada como evidencia. Entrégala al titular por el medio que indicó.</p>
            )}
          </div>
        ) : (
          <>
            <div role="radiogroup" aria-label="Resultado" className="flex flex-wrap gap-4">
              {RESULTADOS.map((r) => (
                <label key={r} className="flex items-center gap-1.5 text-xs ">
                  <input type="radio" name="resultado-respuesta" checked={resultado === r} onChange={() => setResultado(r)} />
                  {etiquetas[r]}
                </label>
              ))}
            </div>
            {modelos.length === 0 ? (
              <p className="text-xs text-[var(--ui-texto-suave)]">
                No hay un modelo para este derecho y resultado. Escribe al equipo de EVYDENTIA para añadirlo.
              </p>
            ) : (
              <>
                <label className="block text-xs ">
                  Modelo de respuesta
                  <select
                    aria-label="Modelo de respuesta"
                    className="mt-1 block w-full rounded border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-1.5"
                    value={modeloId}
                    onChange={(e) => {
                      setModeloId(e.target.value);
                      setValores({});
                    }}
                  >
                    {modelos.map((m, i) => (
                      <option key={m.id} value={m.id}>{`${etiquetas[m.resultado]} · versión ${i + 1}`}</option>
                    ))}
                  </select>
                </label>
                {modelo?.variables.map((v) => {
                  const vacia = !(valores[v] ?? "").trim();
                  return (
                    <div key={v} className="text-xs">
                      <label htmlFor={`var-${v}`}>{etiquetaDeVariable(v)}</label>
                      <input
                        id={`var-${v}`}
                        type="text"
                        className="mt-1 block w-full rounded border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-1.5"
                        value={valores[v] ?? ""}
                        aria-invalid={tocados && vacia}
                        onChange={(e) => setValores({ ...valores, [v]: e.target.value })}
                        onBlur={() => setTocados(true)}
                      />
                      {tocados && vacia && <span className="badge-render-danger">Completa este dato.</span>}
                    </div>
                  );
                })}
                <div role="region" aria-label="Vista previa de la respuesta" className="rounded border border-[var(--ui-borde)] p-3">
                  <h4 className="mb-1 text-xs font-semibold ">Vista previa</h4>
                  <pre className="whitespace-pre-wrap text-xs ">{previa?.texto}</pre>
                </div>
                {permisos.puedeResponder ? (
                  <div className="space-y-2">
                    <button
                      type="button"
                      className={boton}
                      aria-disabled={incompleta}
                      onClick={() => (incompleta ? setTocados(true) : setConfirmando(true))}
                    >
                      Registrar la respuesta
                    </button>
                    {incompleta && (
                      <p className="text-xs text-[var(--ui-texto-suave)]">Completa los datos que faltan en la vista previa.</p>
                    )}
                    <p className="text-xs text-[var(--ui-texto-suave)]">
                      La respuesta queda registrada como evidencia. Entrégala al titular por el medio que indicó en su solicitud.
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-[var(--ui-texto-suave)]">
                    Responde la persona administradora o el implementador de la organización.
                  </p>
                )}
              </>
            )}
          </>
        )}
        {confirmando && (
          <div role="alertdialog" aria-modal="true" aria-label="Registrar la respuesta" className="rounded border border-[var(--ui-borde)] p-3">
            <p className="mb-2 text-xs ">¿Registrar esta respuesta? Después no se puede cambiar.</p>
            <div className="flex gap-2">
              <button type="button" className={boton} autoFocus onClick={() => setConfirmando(false)}>
                Cancelar
              </button>
              <button type="button" className={boton} onClick={() => void alRegistrar()}>
                Registrar la respuesta
              </button>
            </div>
          </div>
        )}
        {error && (
          <p role="alert" className="text-xs badge-render-danger">
            {error}
          </p>
        )}
      </section>
    </div>
  );
}
