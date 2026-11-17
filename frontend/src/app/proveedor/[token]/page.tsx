"use client";

import React, { useState, useEffect, use, useCallback } from "react";
import {
  CuestionarioPublicoInfo,
  obtenerCuestionarioPublico,
  enviarRespuestasPublico,
} from "@/lib/terceros/cuestionario";
import { CheckCircle2, AlertCircle, Upload, Shield, ChevronLeft, ChevronRight } from "lucide-react";

interface Props {
  params: Promise<{ token: string }>;
}

export default function ProveedorPortalPage({ params }: Props) {
  const { token } = use(params);

  const [cargando, setCargando] = useState(true);
  const [info, setInfo] = useState<CuestionarioPublicoInfo | null>(null);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);

  // Estado del asistente
  const [pasoActual, setPasoActual] = useState(0); // 0..N-1 preguntas, N = Revisar y enviar
  const [respuestas, setRespuestas] = useState<Record<string, unknown>>({});
  const [archivos, setArchivos] = useState<{ pregunta_id: string; file: File }[]>([]);
  const [errorPaso, setErrorPaso] = useState<string | null>(null);

  // Envío y confirmación
  const [mostrarConfirmacion, setMostrarConfirmacion] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [enviadoExito, setEnviadoExito] = useState(false);
  const [errorEnvio, setErrorEnvio] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setErrorCarga(null);
    try {
      const data = await obtenerCuestionarioPublico(token);
      setInfo(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("CODIGO_ENLACE_NO_VALIDO") || msg.includes("404") || msg.includes("410")) {
        setErrorCarga("ENLACE_NO_VALIDO");
      } else if (msg.includes("429")) {
        setErrorCarga("DEMASIADOS_INTENTOS");
      } else {
        setErrorCarga("ERROR_GENERICO");
      }
    } finally {
      setCargando(false);
    }
  }, [token]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  if (cargando) {
    return (
      <main className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center p-4">
        <p className="text-zinc-400 text-sm">Cargando el cuestionario…</p>
      </main>
    );
  }

  // Enlace no válido (404 o 410)
  if (errorCarga === "ENLACE_NO_VALIDO") {
    return (
      <main className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-amber-400 mx-auto" />
          <h1 className="text-lg font-bold text-zinc-200">Este enlace ya no está disponible</h1>
          <p className="text-zinc-400 text-xs">
            Puede que haya vencido o que ya se hayan enviado las respuestas. Si necesitas responder, pide un enlace nuevo a la organización que te lo envió.
          </p>
        </div>
      </main>
    );
  }

  if (errorCarga === "DEMASIADOS_INTENTOS") {
    return (
      <main className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
          <p className="text-zinc-300 text-xs">Hubo demasiados intentos. Espera unos minutos e inténtalo de nuevo.</p>
        </div>
      </main>
    );
  }

  if (errorCarga === "ERROR_GENERICO" || !info) {
    return (
      <main className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-center space-y-4">
          <p className="text-zinc-300 text-xs">No pudimos cargar el cuestionario. Vuelve a intentarlo en unos minutos.</p>
          <button
            type="button"
            onClick={cargar}
            className="px-4 py-1.5 bg-emerald-600 text-white rounded font-medium text-xs hover:bg-emerald-500"
          >
            Volver a cargar
          </button>
        </div>
      </main>
    );
  }

  // Éxito al enviar
  if (enviadoExito) {
    return (
      <main className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-zinc-900 border border-emerald-800/60 rounded-xl p-6 text-center space-y-3">
          <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
          <h1 role="status" className="text-lg font-bold text-zinc-100">Respuestas enviadas</h1>
          <p className="text-zinc-300 text-xs">
            Recibimos tus respuestas. {info.organizacion} las revisará. Ya puedes cerrar esta página.
          </p>
        </div>
      </main>
    );
  }

  const preguntas = info.preguntas;
  const totalPasos = preguntas.length + 1; // Preguntas + Revisar y enviar
  const esPasoFinal = pasoActual === preguntas.length;
  const preguntaActual = !esPasoFinal ? preguntas[pasoActual] : null;

  const archivoActual = preguntaActual ? archivos.find((a) => a.pregunta_id === preguntaActual.id) : null;

  const handleArchivoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!preguntaActual || !e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    if (file.size > 10 * 1024 * 1024) {
      setErrorPaso(`El archivo ${file.name} supera los 10 MB.`);
      return;
    }
    setErrorPaso(null);
    setArchivos([...archivos.filter((a) => a.pregunta_id !== preguntaActual.id), { pregunta_id: preguntaActual.id, file }]);
  };

  const quitarArchivo = () => {
    if (!preguntaActual) return;
    setArchivos(archivos.filter((a) => a.pregunta_id !== preguntaActual.id));
  };

  const validarPasoActual = (): boolean => {
    setErrorPaso(null);
    if (!preguntaActual) return true;

    // Condicionales G07 y G15
    if (preguntaActual.id === "G07") {
      const g06 = respuestas["G06"];
      const esSi = g06 === true || String(g06).toLowerCase() === "si" || String(g06).toLowerCase() === "sí";
      if (esSi) {
        if (!respuestas["G07"] || !String(respuestas["G07"]).trim()) {
          setErrorPaso("Completa este paso antes de continuar: describe los subencargados.");
          return false;
        }
        if (!archivoActual) {
          setErrorPaso("Adjunta un documento que respalde tu respuesta.");
          return false;
        }
      }
      return true;
    }

    if (preguntaActual.id === "G15") {
      const g14 = respuestas["G14"];
      const esSi = g14 === true || String(g14).toLowerCase() === "si" || String(g14).toLowerCase() === "sí";
      if (esSi) {
        if (!respuestas["G15"] || !String(respuestas["G15"]).trim()) {
          setErrorPaso("Completa este paso antes de continuar: describe los países y garantías.");
          return false;
        }
        if (!archivoActual) {
          setErrorPaso("Adjunta un documento que respalde tu respuesta.");
          return false;
        }
      }
      return true;
    }

    // Obligatorias generales
    if (preguntaActual.obligatoria) {
      const val = respuestas[preguntaActual.id];
      if (val === undefined || val === null || val === "") {
        setErrorPaso("Completa este paso antes de continuar: responde la pregunta.");
        return false;
      }
      if (preguntaActual.tipo === "si_no_evidencia") {
        const esSi = val === true || String(val).toLowerCase() === "si" || String(val).toLowerCase() === "sí";
        if (esSi && !archivoActual) {
          setErrorPaso("Adjunta un documento que respalde tu respuesta.");
          return false;
        }
      }
    }

    return true;
  };

  const avanzar = () => {
    if (validarPasoActual()) {
      setPasoActual((prev) => Math.min(prev + 1, totalPasos - 1));
    }
  };

  const retroceder = () => {
    setErrorPaso(null);
    setPasoActual((prev) => Math.max(prev - 1, 0));
  };

  const confirmarEnvio = async () => {
    setEnviando(true);
    setErrorEnvio(null);
    try {
      await enviarRespuestasPublico(token, respuestas, archivos);
      setEnviadoExito(true);
    } catch {
      setErrorEnvio("No pudimos enviar tus respuestas. Tus datos siguen en esta página; inténtalo de nuevo.");
      setMostrarConfirmacion(false);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <main
      aria-label={`Cuestionario de garantías para ${info.organizacion}`}
      className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col items-center p-4 sm:p-6"
    >
      <div className="max-w-2xl w-full space-y-6">
        {/* Cabecera */}
        <div className="border-b border-zinc-800 pb-4">
          <div className="flex items-center space-x-2 text-emerald-400 mb-1">
            <Shield className="w-5 h-5" />
            <span className="text-xs font-semibold uppercase tracking-wider">Portal de Proveedores</span>
          </div>
          <h1 className="text-xl font-bold text-zinc-100">
            Cuestionario de garantías para {info.organizacion}
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            {info.organizacion} te pide responder este cuestionario sobre cómo tratas los datos personales que te confía. Puedes adjuntar documentos de respaldo.
          </p>
          <p role="note" className="text-[11px] text-amber-400/90 mt-2 bg-amber-950/20 border border-amber-800/40 rounded p-2">
            Tus respuestas no se guardan hasta que las envíes. Solo puedes enviarlas una vez.
          </p>
        </div>

        {/* Barra de progreso */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-zinc-400 font-medium">
            <span>Paso {pasoActual + 1} de {totalPasos}</span>
            <span>{esPasoFinal ? "Revisar y enviar" : `Pregunta ${pasoActual + 1} de ${preguntas.length}`}</span>
          </div>
          <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-emerald-500 h-full transition-all duration-300"
              style={{ width: `${((pasoActual + 1) / totalPasos) * 100}%` }}
            />
          </div>
        </div>

        {/* Pasos */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
          {!esPasoFinal && preguntaActual ? (
            <div className="space-y-4">
              <div>
                <span className="text-[11px] font-mono text-zinc-500">Referencia: {preguntaActual.cita}</span>
                <h2 className="text-sm font-semibold text-zinc-200 mt-1">{preguntaActual.enunciado}</h2>
              </div>

              {/* Campos según tipo */}
              {(preguntaActual.tipo === "si_no" || preguntaActual.tipo === "si_no_evidencia") && (
                <div className="flex items-center space-x-4 pt-1">
                  <label className="flex items-center space-x-2 cursor-pointer text-xs">
                    <input
                      type="radio"
                      name={preguntaActual.id}
                      checked={respuestas[preguntaActual.id] === true || respuestas[preguntaActual.id] === "si"}
                      onChange={() => {
                        setRespuestas({ ...respuestas, [preguntaActual.id]: true });
                        setErrorPaso(null);
                      }}
                      className="text-emerald-500 focus:ring-0"
                    />
                    <span>Sí</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer text-xs">
                    <input
                      type="radio"
                      name={preguntaActual.id}
                      checked={respuestas[preguntaActual.id] === false || respuestas[preguntaActual.id] === "no"}
                      onChange={() => {
                        setRespuestas({ ...respuestas, [preguntaActual.id]: false });
                        setErrorPaso(null);
                      }}
                      className="text-emerald-500 focus:ring-0"
                    />
                    <span>No</span>
                  </label>
                </div>
              )}

              {(preguntaActual.tipo === "texto" || preguntaActual.tipo === "texto_evidencia") && (
                <div>
                  <textarea
                    value={(respuestas[preguntaActual.id] as string) || ""}
                    onChange={(e) => {
                      setRespuestas({ ...respuestas, [preguntaActual.id]: e.target.value });
                      setErrorPaso(null);
                    }}
                    placeholder="Escribe tu respuesta aquí..."
                    className="w-full bg-zinc-800 border border-zinc-700 rounded p-2.5 text-xs text-zinc-200 h-24 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              )}

              {preguntaActual.tipo === "fecha" && (
                <div>
                  <label htmlFor="campo-fecha" className="block text-xs text-zinc-400 mb-1">
                    {preguntaActual.enunciado}
                  </label>
                  <input
                    id="campo-fecha"
                    type="date"
                    value={(respuestas[preguntaActual.id] as string) || ""}
                    onChange={(e) => {
                      setRespuestas({ ...respuestas, [preguntaActual.id]: e.target.value });
                      setErrorPaso(null);
                    }}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded p-2 text-xs text-zinc-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              )}

              {/* Adjuntos */}
              {(preguntaActual.tipo === "si_no_evidencia" && (respuestas[preguntaActual.id] === true || respuestas[preguntaActual.id] === "si") ||
                preguntaActual.tipo === "texto_evidencia") && (
                <div className="border-t border-zinc-800 pt-3 space-y-2">
                  <span className="block text-xs font-medium text-zinc-300">Documento de respaldo</span>
                  {!archivoActual ? (
                    <div>
                      <label className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded text-xs cursor-pointer border border-zinc-700">
                        <Upload className="w-3.5 h-3.5" />
                        <span>Adjuntar documento</span>
                        <input type="file" onChange={handleArchivoChange} className="hidden" />
                      </label>
                      <span className="block text-[11px] text-zinc-500 mt-1">Hasta 10 MB por archivo.</span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2 text-xs bg-zinc-800/80 border border-zinc-700 px-3 py-1.5 rounded w-fit">
                      <span className="text-zinc-200">{archivoActual.file.name}</span>
                      <button
                        type="button"
                        onClick={quitarArchivo}
                        className="text-rose-400 hover:text-rose-300 underline text-[11px]"
                      >
                        Quitar {archivoActual.file.name}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            /* Paso final: Revisar y enviar */
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-zinc-100">Revisar y enviar</h2>
              <p className="text-xs text-zinc-400">
                Verifica tus respuestas antes de enviarlas. Una vez enviadas no podrás modificarlas.
              </p>

              <ul role="list" aria-label="Pasos del cuestionario" className="divide-y divide-zinc-800 text-xs">
                {preguntas.map((p) => {
                  const val = respuestas[p.id];
                  const arch = archivos.find((a) => a.pregunta_id === p.id);
                  return (
                    <li key={p.id} className="py-2.5">
                      <div className="font-medium text-zinc-300">{p.enunciado}</div>
                      <div className="text-zinc-400 mt-0.5">
                        Respuesta:{" "}
                        <span className="text-zinc-200 font-semibold">
                          {val === true ? "Sí" : val === false ? "No" : String(val || "Sin responder")}
                        </span>
                      </div>
                      {arch && (
                        <div className="text-[11px] text-emerald-400 mt-0.5">
                          Adjunto: {arch.file.name}
                        </div>
                      )}
                    </li>
                  );
                })}
              </ul>

              {errorEnvio && (
                <p role="alert" className="text-rose-400 text-xs">
                  {errorEnvio}
                </p>
              )}
            </div>
          )}

          {errorPaso && (
            <p role="alert" className="text-rose-400 text-xs mt-2">
              {errorPaso}
            </p>
          )}

          {/* Botones de navegación */}
          <div className="flex justify-between items-center pt-3 border-t border-zinc-800">
            <button
              type="button"
              onClick={retroceder}
              disabled={pasoActual === 0}
              className="px-3 py-1.5 bg-zinc-800 text-zinc-400 hover:text-zinc-200 rounded text-xs font-medium flex items-center space-x-1 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Anterior</span>
            </button>

            {!esPasoFinal ? (
              <button
                type="button"
                onClick={avanzar}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold flex items-center space-x-1"
              >
                <span>Siguiente</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setMostrarConfirmacion(true)}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold"
              >
                Enviar respuestas
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Modal de confirmación */}
      {mostrarConfirmacion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-5 max-w-sm w-full text-zinc-100 shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-zinc-100">¿Enviar tus respuestas?</h3>
            <p className="text-xs text-zinc-400">Después no podrás cambiarlas.</p>

            <div className="flex justify-end space-x-2 pt-2 border-t border-zinc-800">
              <button
                type="button"
                autoFocus
                onClick={() => setMostrarConfirmacion(false)}
                className="px-3.5 py-1.5 bg-zinc-800 text-zinc-400 rounded hover:bg-zinc-700 font-medium text-xs"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={enviando}
                aria-busy={enviando}
                onClick={confirmarEnvio}
                className="px-4 py-1.5 bg-emerald-600 text-white rounded font-semibold text-xs hover:bg-emerald-500 disabled:opacity-50"
              >
                {enviando ? "Enviando tus respuestas…" : "Enviar respuestas"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
