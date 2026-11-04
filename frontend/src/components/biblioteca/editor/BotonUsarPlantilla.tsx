"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Botón «Usar en esta organización» (BIB-114).
 * Se monta en la ranura `plantilla:acciones` (BIB-111).
 * Captura las variables de contexto (`texto`, `si_no`, `lista`) y fecha de emisión requeridas por la
 * plantilla y llama a `POST /biblioteca/documentos`.
 * Si el servidor responde 404, 405 o 501, se muestra como no disponible.
 */
import React from "react";
import { obtenerFicha, type FichaPlantilla, type VariablePlantilla } from "@/lib/biblioteca/fichas";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";
import {
  crearDocumento,
  type Documento,
  type TipoVariableContexto,
  type VariableContexto,
} from "@/lib/biblioteca/borradores";

interface VariableNormalizada {
  clave: string;
  etiqueta: string;
  tipo: TipoVariableContexto;
  obligatoria: boolean;
}

function normalizarVariables(ficha: FichaPlantilla): VariableNormalizada[] {
  // Si la ficha trae `variables_contexto` explícita (p. ej. en metadatos o pruebas)
  const explicitas = (ficha as unknown as Record<string, unknown>).variables_contexto as
    | VariableContexto[]
    | undefined;
  if (Array.isArray(explicitas) && explicitas.length > 0) {
    return explicitas.map((v) => ({
      clave: v.clave,
      etiqueta: v.etiqueta || v.clave,
      tipo: v.tipo || "texto",
      obligatoria: v.obligatoria !== false,
    }));
  }

  // De lo contrario, se extraen de `ficha.variables` aquellas cuyo ámbito sea contexto o captura
  return (ficha.variables || [])
    .filter((v: VariablePlantilla) => v.ambito === "contexto" || v.origen === "persona" || v.clave.startsWith("contexto."))
    .map((v: VariablePlantilla) => {
      const vExtra = v as unknown as { tipo?: TipoVariableContexto };
      return {
        clave: v.clave,
        etiqueta: v.etiqueta || v.clave,
        tipo: vExtra.tipo || "texto",
        obligatoria: v.obligatoria !== false,
      };
    });
}

export default function BotonUsarPlantilla() {
  const storePlantillaId = useSeleccionBiblioteca((s) => s.plantillaId);
  const plantillaIdPruebas = typeof window !== "undefined" ? window.__LOPDP_FORMULARIOS_PRUEBAS__?.plantillaId : undefined;
  const plantillaId = storePlantillaId || plantillaIdPruebas || null;
  const elegirDocumento = useSeleccionBiblioteca((s) => s.elegirDocumento);

  const [ficha, setFicha] = React.useState<FichaPlantilla | null>(null);
  const [cargandoFicha, setCargandoFicha] = React.useState(false);
  const [noDisponible, setNoDisponible] = React.useState(false);
  const [errorApi, setErrorApi] = React.useState<string | null>(null);

  const [formularioAbierto, setFormularioAbierto] = React.useState(false);
  const [valores, setValores] = React.useState<Record<string, string>>({});
  const [fechaEmision, setFechaEmision] = React.useState<string>(() => new Date().toISOString().slice(0, 10));
  const [errores, setErrores] = React.useState<Record<string, string>>({});
  const [procesando, setProcesando] = React.useState(false);
  const [documentoCreado, setDocumentoCreado] = React.useState<Documento | null>(null);

  React.useEffect(() => {
    setFicha(null);
    setNoDisponible(false);
    setErrorApi(null);
    setFormularioAbierto(false);
    setDocumentoCreado(null);
    setValores({});
    setErrores({});

    if (!plantillaId) return;

    let vigente = true;
    setCargandoFicha(true);
    obtenerFicha(plantillaId)
      .then((f) => {
        if (!vigente) return;
        setFicha(f);
        // Inicializar valores por defecto para variables tipo si_no
        const vars = normalizarVariables(f);
        const inicial: Record<string, string> = {};
        for (const v of vars) {
          if (v.tipo === "si_no") {
            inicial[v.clave] = "no";
          }
        }
        setValores((prev) => ({ ...inicial, ...prev }));
      })
      .catch((e: unknown) => {
        if (!vigente) return;
        const msg = e instanceof Error ? e.message : "Error al cargar ficha";
        setErrorApi(msg);
      })
      .finally(() => {
        if (vigente) setCargandoFicha(false);
      });

    return () => {
      vigente = false;
    };
  }, [plantillaId]);

  if (!plantillaId) return null;

  const variables = ficha ? normalizarVariables(ficha) : [];

  function actualizarValor(clave: string, valor: string) {
    setValores((prev) => ({ ...prev, [clave]: valor }));
    if (errores[clave]) {
      setErrores((prev) => {
        const copia = { ...prev };
        delete copia[clave];
        return copia;
      });
    }
  }

  async function ejecutarCreacion(contextoPreparado: Record<string, string | string[]>) {
    if (!plantillaId) return;
    setProcesando(true);
    setErrorApi(null);

    const resultado = await crearDocumento({
      plantilla_id: plantillaId,
      fecha_emision: fechaEmision || undefined,
      contexto: contextoPreparado,
    });

    setProcesando(false);

    if (resultado.estado === "no_disponible") {
      setNoDisponible(true);
      setFormularioAbierto(false);
      return;
    }

    if (resultado.estado === "denegado") {
      setErrorApi(resultado.mensaje);
      return;
    }

    if (resultado.estado === "error") {
      setErrorApi(resultado.mensaje);
      return;
    }

    setDocumentoCreado(resultado.documento);
    setFormularioAbierto(false);
    elegirDocumento(resultado.documento.id);
  }

  function handleIniciar() {
    setErrorApi(null);
    setDocumentoCreado(null);
    if (variables.length > 0) {
      setFormularioAbierto(true);
    } else {
      void ejecutarCreacion({});
    }
  }

  function handleConfirmar(e: React.FormEvent) {
    e.preventDefault();
    const nuevosErrores: Record<string, string> = {};

    for (const v of variables) {
      const val = valores[v.clave];
      if (v.obligatoria) {
        if (!val || val.trim() === "") {
          nuevosErrores[v.clave] = "Este campo es obligatorio.";
        }
      }
    }

    if (Object.keys(nuevosErrores).length > 0) {
      setErrores(nuevosErrores);
      return;
    }

    // Preparar contexto respetando tipos
    const contextoFinal: Record<string, string | string[]> = {};
    for (const v of variables) {
      const val = valores[v.clave] || "";
      if (v.tipo === "lista") {
        const items = val
          .split(/[\n,]+/)
          .map((s) => s.trim())
          .filter(Boolean);
        contextoFinal[v.clave] = items;
      } else if (v.tipo === "si_no") {
        contextoFinal[v.clave] = val === "si" ? "si" : "no";
      } else {
        contextoFinal[v.clave] = val.trim();
      }
    }

    void ejecutarCreacion(contextoFinal);
  }

  return (
    <div data-testid="acciones-usar-plantilla" className="flex flex-col gap-2">
      {noDisponible ? (
        <div className="flex flex-col gap-1">
          <button
            type="button"
            disabled
            aria-disabled="true"
            data-testid="boton-usar-plantilla"
            className="rounded-md border border-[var(--ui-borde)] bg-zinc-100 dark:bg-zinc-800 px-3 py-1.5 font-medium text-[var(--ui-texto-suave)] cursor-not-allowed opacity-60"
          >
            No disponible
          </button>
          <p role="status" className="text-xs text-amber-700 dark:text-amber-300">
            La creación de documentos desde esta plantilla no está disponible en este momento.
          </p>
        </div>
      ) : (
        <button
          type="button"
          onClick={handleIniciar}
          disabled={cargandoFicha || procesando}
          data-testid="boton-usar-plantilla"
          className="cursor-pointer rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton-hover)] px-3 py-1.5 font-medium hover:bg-zinc-200 dark:hover:bg-zinc-700 disabled:opacity-60"
        >
          {procesando ? "Creando borrador…" : "Usar en esta organización"}
        </button>
      )}

      {errorApi && (
        <p role="alert" data-testid="alerta-error-usar" className="text-xs text-red-700 dark:text-red-300">
          {errorApi}
        </p>
      )}

      {documentoCreado && (
        <p role="status" data-testid="mensaje-documento-creado" className="text-xs text-green-700 dark:text-green-300">
          Documento creado en borrador
          {documentoCreado.variables_faltantes?.length > 0 &&
            ` · faltan ${documentoCreado.variables_faltantes.length} datos para pasar a revisión`}.
        </p>
      )}

      {formularioAbierto && (
        <div
          role="dialog"
          aria-labelledby="titulo-formulario-contexto"
          data-testid="formulario-variables-contexto"
          className="mt-2 flex flex-col gap-3 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-3 text-xs"
        >
          <h4 id="titulo-formulario-contexto" className="text-sm font-semibold">
            Variables de contexto para el borrador
          </h4>
          <p className="text-[var(--ui-texto-suave)]">
            Complete las variables requeridas por la plantilla para generar el borrador.
          </p>

          <form onSubmit={handleConfirmar} className="flex flex-col gap-3">
            <div className="flex flex-col gap-1">
              <label htmlFor="campo-fecha-emision" className="font-medium">
                Fecha de emisión
              </label>
              <input
                id="campo-fecha-emision"
                type="date"
                data-testid="input-fecha-emision"
                value={fechaEmision}
                onChange={(e) => setFechaEmision(e.target.value)}
                className="rounded border border-[var(--ui-borde)] px-2 py-1 bg-white dark:bg-zinc-900"
              />
            </div>

            {variables.map((v) => (
              <div key={v.clave} className="flex flex-col gap-1">
                <label htmlFor={`campo-${v.clave}`} className="font-medium">
                  {v.etiqueta} {v.obligatoria && <span className="text-red-600">*</span>}
                </label>

                {v.tipo === "si_no" ? (
                  <select
                    id={`campo-${v.clave}`}
                    data-testid={`select-${v.clave}`}
                    value={valores[v.clave] || "no"}
                    onChange={(e) => actualizarValor(v.clave, e.target.value)}
                    className="rounded border border-[var(--ui-borde)] px-2 py-1 bg-white dark:bg-zinc-900"
                  >
                    <option value="si">Sí</option>
                    <option value="no">No</option>
                  </select>
                ) : v.tipo === "lista" ? (
                  <textarea
                    id={`campo-${v.clave}`}
                    data-testid={`textarea-${v.clave}`}
                    rows={3}
                    placeholder="Ingrese elementos separados por línea o coma"
                    value={valores[v.clave] || ""}
                    onChange={(e) => actualizarValor(v.clave, e.target.value)}
                    className="rounded border border-[var(--ui-borde)] px-2 py-1 bg-white dark:bg-zinc-900"
                  />
                ) : (
                  <input
                    id={`campo-${v.clave}`}
                    type="text"
                    data-testid={`input-${v.clave}`}
                    value={valores[v.clave] || ""}
                    onChange={(e) => actualizarValor(v.clave, e.target.value)}
                    className="rounded border border-[var(--ui-borde)] px-2 py-1 bg-white dark:bg-zinc-900"
                  />
                )}

                {errores[v.clave] && (
                  <span role="alert" className="text-red-600 text-xs font-medium">
                    {errores[v.clave]}
                  </span>
                )}
              </div>
            ))}

            <div className="flex items-center gap-2 pt-2">
              <button
                type="submit"
                disabled={procesando}
                data-testid="boton-confirmar-creacion"
                className="cursor-pointer rounded-md bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 font-medium disabled:opacity-60"
              >
                {procesando ? "Creando…" : "Crear borrador"}
              </button>
              <button
                type="button"
                onClick={() => setFormularioAbierto(false)}
                disabled={procesando}
                data-testid="boton-cancelar"
                className="cursor-pointer rounded-md border border-[var(--ui-borde)] px-3 py-1.5 font-medium hover:bg-[var(--ui-boton-hover)]"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
