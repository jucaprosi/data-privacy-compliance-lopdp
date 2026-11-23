// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  listarMisParticipaciones,
  iniciarExamen,
  obtenerExamen,
  enviarExamen,
  type MiParticipacion,
  type ExamenDetalle,
  type PreguntaFormativa,
} from "../../lib/formacion/formacion";

export const MiFormacion: React.FC = () => {
  const [participaciones, setParticipaciones] = useState<MiParticipacion[]>([]);
  const [seleccionada, setSeleccionada] = useState<MiParticipacion | null>(null);
  const [examen, setExamen] = useState<ExamenDetalle | null>(null);
  const [respuestas, setRespuestas] = useState<Record<number, number>>({});
  const [cargando, setCargando] = useState<boolean>(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  const [errorEnvio, setErrorEnvio] = useState<string | null>(null);
  const [intentoNoConsumido, setIntentoNoConsumido] = useState<boolean>(false);
  const [mostrarModalConfirmacion, setMostrarModalConfirmacion] = useState<boolean>(false);
  const [enviando, setEnviando] = useState<boolean>(false);
  const [resultado, setResultado] = useState<{
    aprobado: boolean;
    nota: number;
    minima: number;
    diplomaSha256?: string;
  } | null>(null);

  const botonCancelarRef = useRef<HTMLButtonElement>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setErrorCarga(null);
    try {
      const data = await listarMisParticipaciones();
      setParticipaciones(data);
      setSeleccionada((actual) => actual
        ? data.find((p) => p.id === actual.id) ?? null
        : data[0] ?? null);
    } catch {
      setErrorCarga("No pudimos cargar la formación. Inténtalo de nuevo.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  useEffect(() => {
    if (mostrarModalConfirmacion && botonCancelarRef.current) {
      botonCancelarRef.current.focus();
    }
  }, [mostrarModalConfirmacion]);

  const seleccionarParticipacion = (part: MiParticipacion) => {
    setSeleccionada(part);
    setExamen(null);
    setRespuestas({});
    setErrorEnvio(null);
    setIntentoNoConsumido(false);
    setResultado(
      part.terminado_en
        ? {
            aprobado: (part.nota ?? 0) >= part.nota_minima,
            nota: part.nota ?? 0,
            minima: part.nota_minima,
            diplomaSha256: part.diploma_sha256 ?? undefined,
          }
        : null
    );
  };

  const comenzarExamen = async () => {
    if (!seleccionada) return;
    setErrorEnvio(null);
    setIntentoNoConsumido(false);
    try {
      await iniciarExamen(seleccionada.id);
      const ex = await obtenerExamen(seleccionada.id);
      setExamen(ex);
      setRespuestas({});
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("ACCION_FUERA_DE_FECHAS")) {
        setErrorEnvio(
          `Esta formación se puede rendir del ${seleccionada.inicio} al ${seleccionada.fin}.`
        );
      } else if (msg.includes("EXAMEN_YA_RENDIDO")) {
        setErrorEnvio("Ya rendiste este examen.");
      } else {
        setErrorEnvio("No pudimos iniciar el examen. Inténtalo de nuevo.");
      }
    }
  };

  const responderPregunta = (preguntaIndex: number, opcionIndex: number) => {
    setRespuestas((prev) => ({
      ...prev,
      [preguntaIndex]: opcionIndex,
    }));
  };

  const totalPreguntas = examen?.preguntas.length ?? 0;
  const respondidasCount = Object.keys(respuestas).length;
  const faltantes = totalPreguntas - respondidasCount;
  const formularioCompleto = totalPreguntas > 0 && faltantes === 0;

  const confirmarEnvio = async () => {
    if (!seleccionada || !examen) return;
    setEnviando(true);
    setErrorEnvio(null);
    setIntentoNoConsumido(false);
    setMostrarModalConfirmacion(false);

    // Array de números con el índice de la opción para cada pregunta
    const payloadRespuestas: number[] = [];
    for (let i = 0; i < totalPreguntas; i++) {
      payloadRespuestas.push(respuestas[i] ?? 0);
    }

    try {
      const res = await enviarExamen(seleccionada.id, payloadRespuestas);
      setResultado({
        aprobado: res.aprobado,
        nota: res.nota,
        minima: seleccionada.nota_minima,
        diplomaSha256: res.diploma_sha256 ?? undefined,
      });
      setExamen(null);
      void cargar();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("EXAMEN_YA_RENDIDO")) {
        setErrorEnvio("Ya rendiste este examen.");
      } else if (msg.includes("ACCION_FUERA_DE_FECHAS")) {
        setErrorEnvio(
          `Esta formación se puede rendir del ${seleccionada.inicio} al ${seleccionada.fin}.`
        );
      } else {
        setErrorEnvio("No pudimos enviar tus respuestas. Inténtalo de nuevo.");
        setIntentoNoConsumido(true);
      }
    } finally {
      setEnviando(false);
    }
  };

  if (cargando) {
    return (
      <main aria-label="Mi formación" className="p-6">
        <h1 className="text-2xl font-bold text-[var(--ui-text-primary)]">Mi formación</h1>
        <p className="mt-4 text-[var(--ui-text-secondary)]">Cargando tus formaciones...</p>
      </main>
    );
  }

  if (errorCarga) {
    return (
      <main aria-label="Mi formación" className="p-6">
        <h1 className="text-2xl font-bold text-[var(--ui-text-primary)]">Mi formación</h1>
        <div role="alert" className="mt-4 p-4 rounded bg-red-100 text-red-900 border border-red-300">
          <p>{errorCarga}</p>
          <button
            onClick={() => void cargar()}
            className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
          >
            Volver a cargar
          </button>
        </div>
      </main>
    );
  }

  return (
    <main aria-label="Mi formación" className="p-6 max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-[var(--ui-text-primary)]">Mi formación</h1>

      {participaciones.length === 0 ? (
        <p className="text-[var(--ui-text-secondary)]">No tienes capacitaciones asignadas actualmente.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Lista de participaciones */}
          <section aria-label="Lista de capacitaciones" className="space-y-3">
            <h2 className="text-lg font-semibold text-[var(--ui-text-primary)]">Tus capacitaciones</h2>
            <div className="space-y-2">
              {participaciones.map((p) => {
                const seleccionadaActiva = seleccionada?.id === p.id;
                let estadoTexto = "Enviada";
                let badgeClase = "bg-blue-100 text-blue-800";
                if (p.terminado_en) {
                  const aprobo = (p.nota ?? 0) >= p.nota_minima;
                  if (aprobo) {
                    estadoTexto = "Aprobó";
                    badgeClase = "bg-green-100 text-green-800";
                  } else {
                    estadoTexto = "No aprobó";
                    badgeClase = "bg-red-100 text-red-800";
                  }
                } else if (p.iniciado_en) {
                  estadoTexto = "Iniciada";
                  badgeClase = "bg-amber-100 text-amber-800";
                }

                return (
                  <button
                    key={p.id}
                    onClick={() => seleccionarParticipacion(p)}
                    className={`w-full text-left p-3 rounded border transition-colors ${
                      seleccionadaActiva
                        ? "border-[var(--ui-primary)] bg-[var(--ui-primary-subtle,#eef2ff)]"
                        : "border-[var(--ui-border)] hover:bg-[var(--ui-hover,#f9fafb)]"
                    }`}
                  >
                    <div className="font-medium text-[var(--ui-text-primary)]">{p.accion_nombre}</div>
                    <div className="text-xs text-[var(--ui-text-secondary)] mt-1">
                      Del {p.inicio} al {p.fin}
                    </div>
                    <div className="mt-2">
                      <span className={`inline-block px-2 py-0.5 text-xs font-semibold rounded ${badgeClase}`}>
                        {estadoTexto}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </section>

          {/* Detalle y Examen */}
          <section aria-label="Detalle de formación" className="md:col-span-2 space-y-6">
            {seleccionada && (
              <div className="border border-[var(--ui-border)] rounded-lg p-5 bg-[var(--ui-surface,#ffffff)] space-y-6">
                <div>
                  <h2 className="text-xl font-bold text-[var(--ui-text-primary)]">{seleccionada.accion_nombre}</h2>
                  <p className="text-sm text-[var(--ui-text-secondary)] mt-1">
                    Disponible del {seleccionada.inicio} al {seleccionada.fin} · Nota mínima: {seleccionada.nota_minima}
                  </p>
                </div>

                {/* Mensajes de error */}
                {errorEnvio && (
                  <div role="alert" className="p-3 bg-red-100 text-red-900 border border-red-300 rounded text-sm">
                    <p>{errorEnvio}</p>
                    {intentoNoConsumido && (
                      <p className="mt-1 font-semibold">Tu intento no se ha consumido.</p>
                    )}
                  </div>
                )}

                {/* Resultado ya rendido */}
                {resultado ? (
                  <div
                    role="status"
                    className={`p-4 rounded border text-sm ${
                      resultado.aprobado
                        ? "bg-green-50 border-green-200 text-green-900"
                        : "bg-red-50 border-red-200 text-red-900"
                    }`}
                  >
                    {resultado.aprobado ? (
                      <div>
                        <p className="font-semibold text-base">
                          Aprobaste con {resultado.nota}. Tu constancia de formación quedó guardada.
                        </p>
                        {resultado.diplomaSha256 && (
                          <div className="mt-3">
                            <span className="text-xs text-[var(--ui-text-secondary)] block mb-1">
                              Constancia custodiada bajo hash de verificación
                            </span>
                            <span className="text-sm font-medium text-[var(--ui-primary)] inline-block px-3 py-1 bg-white border border-green-400 rounded">
                              Abrir tu constancia
                            </span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="font-medium text-base">
                        No alcanzaste la nota mínima ({resultado.nota} de {resultado.minima}). Consulta con tu coordinador cómo continuar.
                      </p>
                    )}
                  </div>
                ) : (
                  /* Flujo de Examen */
                  <div className="border-t border-[var(--ui-border)] pt-5 space-y-4">
                    <h3 className="text-lg font-bold text-[var(--ui-text-primary)]">Examen</h3>

                    {!examen ? (
                      <div className="space-y-4">
                        <div className="p-4 bg-amber-50 border border-amber-200 rounded text-sm text-amber-900">
                          <p className="font-medium">
                            Tienes un solo intento. Una vez que lo envíes no podrás repetirlo. Nota mínima: {seleccionada.nota_minima}.
                          </p>
                        </div>
                        <button
                          onClick={() => void comenzarExamen()}
                          className="px-4 py-2 bg-[var(--ui-primary)] text-white rounded font-medium hover:opacity-90"
                        >
                          Empezar el examen
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        {examen.preguntas.map((p: PreguntaFormativa, idx: number) => (
                          <fieldset
                            key={p.id}
                            role="radiogroup"
                            aria-labelledby={`enunciado-${p.id}`}
                            className="p-4 border border-[var(--ui-border)] rounded-md space-y-3"
                          >
                            <legend id={`enunciado-${p.id}`} className="font-semibold text-[var(--ui-text-primary)]">
                              {idx + 1}. {p.enunciado}
                            </legend>
                            <div className="space-y-2 mt-2">
                              {p.opciones.map((opcTexto: string, opcIdx: number) => {
                                const checked = respuestas[idx] === opcIdx;
                                return (
                                  <label
                                    key={opcIdx}
                                    className={`flex items-center space-x-3 p-2 rounded cursor-pointer border transition-colors ${
                                      checked
                                        ? "border-[var(--ui-primary)] bg-[var(--ui-primary-subtle,#f0fdf4)]"
                                        : "border-transparent hover:bg-[var(--ui-hover,#f9fafb)]"
                                    }`}
                                  >
                                    <input
                                      type="radio"
                                      name={`pregunta-${p.id}`}
                                      value={opcIdx}
                                      checked={checked}
                                      onChange={() => responderPregunta(idx, opcIdx)}
                                      className="h-4 w-4 text-[var(--ui-primary)] focus:ring-[var(--ui-primary)]"
                                    />
                                    <span className="text-sm text-[var(--ui-text-primary)]">{opcTexto}</span>
                                  </label>
                                );
                              })}
                            </div>
                          </fieldset>
                        ))}

                        <div className="pt-2">
                          <button
                            type="button"
                            aria-disabled={!formularioCompleto || enviando}
                            disabled={!formularioCompleto || enviando}
                            onClick={() => setMostrarModalConfirmacion(true)}
                            className={`px-5 py-2.5 rounded font-medium text-white transition-opacity ${
                              !formularioCompleto || enviando
                                ? "bg-gray-400 cursor-not-allowed opacity-60"
                                : "bg-[var(--ui-primary)] hover:opacity-90"
                            }`}
                          >
                            Enviar respuestas
                          </button>
                          {!formularioCompleto && (
                            <p className="mt-2 text-xs text-amber-700">
                              Te faltan {faltantes} preguntas por responder.
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </section>
        </div>
      )}

      {/* Modal de confirmación */}
      {mostrarModalConfirmacion && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="titulo-modal"
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
        >
          <div className="bg-[var(--ui-surface,#ffffff)] rounded-lg p-6 max-w-md w-full border border-[var(--ui-border)] shadow-xl space-y-4">
            <h3 id="titulo-modal" className="text-lg font-bold text-[var(--ui-text-primary)]">
              ¿Enviar tus respuestas?
            </h3>
            <p className="text-sm text-[var(--ui-text-secondary)]">
              Tienes un solo intento y no podrás cambiarlas después.
            </p>
            <div className="flex justify-end space-x-3 pt-2">
              <button
                ref={botonCancelarRef}
                type="button"
                onClick={() => setMostrarModalConfirmacion(false)}
                className="px-4 py-2 border border-[var(--ui-border)] rounded text-sm font-medium hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => void confirmarEnvio()}
                className="px-4 py-2 bg-[var(--ui-primary)] text-white rounded text-sm font-medium hover:opacity-90"
              >
                Enviar respuestas
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
};
