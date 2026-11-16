// ¤evidencias ¤rbac-tenant
import React, { useState, useEffect } from "react";
import {
  ContenidoFormativo,
  PreguntaFormativa,
  listarContenidos,
  crearContenido,
  listarPreguntas,
  crearPregunta,
} from "@/lib/formacion/formacion";

interface Props {
  puedeGestionar: boolean;
}

export const ContenidosPanel: React.FC<Props> = ({ puedeGestionar }) => {
  const [contenidos, setContenidos] = useState<ContenidoFormativo[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Diálogo Nuevo Contenido
  const [mostrarCrear, setMostrarCrear] = useState(false);
  const [titulo, setTitulo] = useState("");
  const [tipo, setTipo] = useState<"pdf" | "video">("pdf");
  const [referencia, setReferencia] = useState("");
  const [guardando, setGuardando] = useState(false);

  // Banco de preguntas de un contenido
  const [contenidoSeleccionado, setContenidoSeleccionado] = useState<ContenidoFormativo | null>(null);
  const [preguntas, setPreguntas] = useState<PreguntaFormativa[]>([]);
  const [enunciado, setEnunciado] = useState("");
  const [opcionesTexto, setOpcionesTexto] = useState("");
  const [correcta, setCorrecta] = useState(0);
  const [errorPregunta, setErrorPregunta] = useState<string | null>(null);

  const cargar = async () => {
    setCargando(true);
    setError(null);
    try {
      const data = await listarContenidos();
      setContenidos(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "No pudimos cargar los contenidos.");
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  const handleCrearContenido = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!titulo.trim() || !referencia.trim()) return;

    setGuardando(true);
    try {
      await crearContenido({ titulo: titulo.trim(), tipo, referencia: referencia.trim() });
      setMostrarCrear(false);
      setTitulo("");
      setReferencia("");
      await cargar();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al crear contenido.");
    } finally {
      setGuardando(false);
    }
  };

  const handleVerPreguntas = async (c: ContenidoFormativo) => {
    setContenidoSeleccionado(c);
    setErrorPregunta(null);
    try {
      const lista = await listarPreguntas(c.id);
      setPreguntas(lista);
    } catch (err: unknown) {
      setErrorPregunta(err instanceof Error ? err.message : "Error al cargar preguntas.");
    }
  };

  const handleCrearPregunta = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!contenidoSeleccionado || !enunciado.trim()) return;

    const ops = opcionesTexto.split("\n").map((s) => s.trim()).filter(Boolean);
    if (ops.length < 2 || ops.length > 6) {
      setErrorPregunta("Escribe entre 2 y 6 opciones (una por línea).");
      return;
    }

    try {
      await crearPregunta(contenidoSeleccionado.id, {
        enunciado: enunciado.trim(),
        opciones: ops,
        correcta: Number(correcta),
      });
      setEnunciado("");
      setOpcionesTexto("");
      setCorrecta(0);
      const lista = await listarPreguntas(contenidoSeleccionado.id);
      setPreguntas(lista);
    } catch (err: unknown) {
      setErrorPregunta(err instanceof Error ? err.message : "Error al guardar pregunta.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">Contenidos formativos</h2>
          <p className="text-xs text-slate-500">Documentos PDF y enlaces a video con sus bancos de preguntas.</p>
        </div>
        {puedeGestionar && (
          <button
            type="button"
            onClick={() => setMostrarCrear(true)}
            className="rounded bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500"
          >
            Nuevo contenido
          </button>
        )}
      </div>

      {cargando ? (
        <div role="status" className="p-4 text-sm text-slate-500">
          Cargando contenidos formativos...
        </div>
      ) : error ? (
        <div role="alert" className="p-4 bg-rose-50 text-rose-800 rounded text-sm">
          {error}
        </div>
      ) : contenidos.length === 0 ? (
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 text-center text-sm text-slate-500">
          Aún no hay contenidos. Añade un PDF o un enlace a un video.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {contenidos.map((c) => (
            <div
              key={c.id}
              className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm space-y-3 flex flex-col justify-between"
            >
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                    {c.tipo}
                  </span>
                  <span className="text-xs text-slate-400">
                    {new Date(c.creado_en).toLocaleDateString()}
                  </span>
                </div>
                <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
                  {c.titulo}
                </h3>
                <p className="text-xs text-slate-500 truncate" title={c.referencia}>
                  {c.referencia}
                </p>
              </div>

              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center">
                <button
                  type="button"
                  onClick={() => handleVerPreguntas(c)}
                  className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
                >
                  Banco de preguntas →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal / Panel Banco de Preguntas */}
      {contenidoSeleccionado && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4"
        >
          <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-lg bg-white dark:bg-slate-900 p-6 shadow-xl border border-slate-200 dark:border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b pb-3 border-slate-100 dark:border-slate-800">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Preguntas del examen: {contenidoSeleccionado.titulo}
                </h3>
                <p className="text-xs text-slate-500">Cada persona rinde el examen una sola vez.</p>
              </div>
              <button
                type="button"
                onClick={() => setContenidoSeleccionado(null)}
                className="text-slate-400 hover:text-slate-600 text-sm"
              >
                ✕ Cerrar
              </button>
            </div>

            {errorPregunta && (
              <div role="alert" className="text-xs text-rose-600 font-medium">
                {errorPregunta}
              </div>
            )}

            {/* Lista de preguntas existentes */}
            <div className="space-y-3">
              {preguntas.length === 0 ? (
                <p className="text-xs text-slate-500 italic">No hay preguntas registradas en este contenido.</p>
              ) : (
                preguntas.map((p) => (
                  <div key={p.id} className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded border border-slate-100 dark:border-slate-800 text-xs space-y-1">
                    <div className="font-semibold text-slate-800 dark:text-slate-200">
                      {p.orden + 1}. {p.enunciado}
                    </div>
                    <ul className="list-disc list-inside space-y-0.5 text-slate-600 dark:text-slate-400">
                      {p.opciones.map((op, idx) => (
                        <li key={idx} className={idx === p.correcta ? "font-bold text-emerald-600 dark:text-emerald-400" : ""}>
                          {op} {idx === p.correcta && "(Respuesta correcta)"}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))
              )}
            </div>

            {/* Formulario para añadir pregunta */}
            {puedeGestionar && (
              <form onSubmit={handleCrearPregunta} className="border-t pt-4 space-y-3">
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase">
                  Añadir pregunta
                </h4>
                <div>
                  <label className="text-xs text-slate-600 dark:text-slate-400 font-medium">Enunciado</label>
                  <input
                    type="text"
                    required
                    value={enunciado}
                    onChange={(e) => setEnunciado(e.target.value)}
                    placeholder="¿Cuál es la finalidad de la LOPDP?"
                    className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-600 dark:text-slate-400 font-medium">Opciones (una por línea, 2 a 6)</label>
                  <textarea
                    rows={3}
                    required
                    value={opcionesTexto}
                    onChange={(e) => setOpcionesTexto(e.target.value)}
                    placeholder={"Garantizar la protección de datos personales\nPromover el comercio informal"}
                    className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 p-2 text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-600 dark:text-slate-400 font-medium">Índice opción correcta (0 para primera opción, 1 para segunda...)</label>
                  <input
                    type="number"
                    min={0}
                    max={5}
                    value={correcta}
                    onChange={(e) => setCorrecta(Number(e.target.value))}
                    className="w-20 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-xs"
                  />
                </div>
                <div className="flex justify-end">
                  <button
                    type="submit"
                    className="rounded bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500"
                  >
                    Guardar pregunta
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Modal Crear Contenido */}
      {mostrarCrear && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4"
        >
          <form
            onSubmit={handleCrearContenido}
            className="w-full max-w-md rounded-lg bg-white dark:bg-slate-900 p-6 shadow-xl border border-slate-200 dark:border-slate-800 space-y-4"
          >
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
              Nuevo contenido
            </h3>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Título</label>
              <input
                type="text"
                required
                value={titulo}
                onChange={(e) => setTitulo(e.target.value)}
                placeholder="Inducción general a la LOPDP"
                className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Tipo</label>
              <select
                value={tipo}
                onChange={(e) => setTipo(e.target.value as "pdf" | "video")}
                className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs"
              >
                <option value="pdf">PDF</option>
                <option value="video">Video</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Enlace o documento</label>
              <input
                type="text"
                required
                value={referencia}
                onChange={(e) => setReferencia(e.target.value)}
                placeholder="https://ejemplo.com/material.pdf"
                className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                autoFocus
                onClick={() => setMostrarCrear(false)}
                className="rounded border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-xs font-medium"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={guardando}
                className="rounded bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {guardando ? "Creando..." : "Crear contenido"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
