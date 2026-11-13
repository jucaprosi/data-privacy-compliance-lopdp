"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Plantillas de la cuenta profesional (BIB-401): copias de las maestras con la marca y el criterio de la cuenta.
 *
 * Se monta en la ranura `pestana:plantillas` desde `vistas/index.ts`. Solo para quien tiene el rol
 * `implementador`; sin él (o si el servidor responde 403) la vista no se pinta. Nunca se muestra el texto
 * de error del servidor: cada fallo tiene un mensaje fijo.
 */
import React, { useCallback, useEffect, useRef, useState } from "react";
import { GitCompare, Check, RefreshCw, Briefcase } from "lucide-react";
import {
  ErrorPlantillasCuenta,
  aplicarMaestra,
  esImplementador,
  listarPlantillasCuenta,
  obtenerDiffMaestra,
  type DiffMaestra,
  type PlantillaCuenta,
} from "@/lib/biblioteca/plantillasCuenta";
import ModalDiffMaestra from "./ModalDiffMaestra";

const MSG_CARGA = "No pudimos cargar tus plantillas. Inténtalo de nuevo.";
const MSG_DIFF = "No pudimos traer las diferencias con la maestra. Inténtalo de nuevo.";
const MSG_APLICAR = "No pudimos aplicar la versión de la maestra. La copia sigue como estaba.";

const ETIQUETA = {
  vigente: { texto: "Vigente", clase: "badge-render-success", id: "badge-vigente" },
  desactualizada: { texto: "Desactualizada", clase: "badge-render-warning", id: "badge-desactualizada" },
  retirada: {
    texto: "Retirada",
    clase: "border border-[var(--ui-borde)] bg-[var(--ui-campo)] text-[var(--ui-texto-suave)]",
    id: "badge-retirada",
  },
} as const;

/** Nombre de marca legible, si la copia lo trae; nunca se imprime el objeto. React lo escapa como texto. */
function nombreDeMarca(marca: PlantillaCuenta["marca"]): string | null {
  const nombre = marca && typeof marca === "object" ? (marca as Record<string, unknown>).nombre : null;
  return typeof nombre === "string" && nombre.trim() ? nombre.trim() : null;
}

export default function VistaPlantillasCuenta() {
  const [esImp, setEsImp] = useState<boolean | null>(null);
  const [copias, setCopias] = useState<PlantillaCuenta[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [denegado, setDenegado] = useState(false);

  const [copiaDiff, setCopiaDiff] = useState<PlantillaCuenta | null>(null);
  const [diff, setDiff] = useState<DiffMaestra | null>(null);
  const [cargandoDiff, setCargandoDiff] = useState(false);
  const [aplicando, setAplicando] = useState(false);
  const [errorAplicar, setErrorAplicar] = useState<string | null>(null);
  const disparador = useRef<HTMLElement | null>(null);

  useEffect(() => {
    let activo = true;
    esImplementador().then((permitido) => {
      if (activo) setEsImp(permitido);
    });
    return () => {
      activo = false;
    };
  }, []);

  const recargar = useCallback(async () => {
    if (esImp !== true) return;
    setCargando(true);
    setError(null);
    try {
      setCopias(await listarPlantillasCuenta());
    } catch (err) {
      if (err instanceof ErrorPlantillasCuenta && err.estado === 403) setDenegado(true);
      else setError(MSG_CARGA);
    } finally {
      setCargando(false);
    }
  }, [esImp]);

  useEffect(() => {
    if (esImp === true) void recargar();
  }, [esImp, recargar]);

  if (esImp !== true || denegado) return null;

  function cerrarComparacion() {
    setCopiaDiff(null);
    setDiff(null);
    setErrorAplicar(null);
    const volver = disparador.current;
    disparador.current = null;
    requestAnimationFrame(() => volver?.focus());
  }

  async function comparar(copia: PlantillaCuenta, boton: HTMLElement) {
    disparador.current = boton;
    setError(null);
    setErrorAplicar(null);
    setCopiaDiff(copia);
    setDiff(null);
    setCargandoDiff(true);
    try {
      setDiff(await obtenerDiffMaestra(copia.id));
    } catch {
      setCopiaDiff(null);
      setError(MSG_DIFF);
    } finally {
      setCargandoDiff(false);
    }
  }

  async function aplicar(copia: PlantillaCuenta) {
    setAplicando(true);
    setErrorAplicar(null);
    setError(null);
    try {
      await aplicarMaestra(copia.id);
      cerrarComparacion();
      await recargar();
    } catch {
      if (copiaDiff) setErrorAplicar(MSG_APLICAR);
      else setError(MSG_APLICAR);
    } finally {
      setAplicando(false);
    }
  }

  return (
    <section
      aria-labelledby="titulo-plantillas-cuenta"
      data-testid="vista-plantillas-cuenta"
      className="mt-6 flex flex-col gap-4 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-fondo)] p-4 text-xs"
    >
      <div className="flex flex-wrap items-start justify-between gap-2 border-b border-[var(--ui-borde)] pb-3">
        <div className="flex items-start gap-2">
          <Briefcase className="mt-0.5 h-4 w-4 text-[var(--ui-primario)]" aria-hidden="true" />
          <div>
            <h3 id="titulo-plantillas-cuenta" className="text-sm font-semibold">
              Plantillas de tu cuenta profesional
            </h3>
            <p className="text-[var(--ui-texto-suave)]">
              Copias de las plantillas maestras con la marca y el criterio de tu cuenta. Puedes usarlas en varias organizaciones.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => void recargar()}
          disabled={cargando}
          aria-busy={cargando}
          className="flex items-center gap-1 rounded-md border border-[var(--ui-borde)] px-2.5 py-1 text-xs hover:bg-[var(--ui-boton-hover)] cursor-pointer"
        >
          <RefreshCw className="h-3 w-3" aria-hidden="true" />
          <span>Volver a cargar</span>
        </button>
      </div>

      {error && (
        <p role="alert" className="badge-render-danger rounded-md p-2.5 text-xs">
          {error}
        </p>
      )}

      {cargando && copias.length === 0 ? (
        <p role="status" className="py-6 text-center text-[var(--ui-texto-suave)]">
          Cargando las plantillas de tu cuenta…
        </p>
      ) : copias.length === 0 ? (
        !error && (
          <p className="py-6 text-center text-[var(--ui-texto-suave)]">
            Aún no tienes copias de plantillas en tu cuenta profesional. Se crean a partir de una plantilla maestra publicada.
          </p>
        )
      ) : (
        <ul data-testid="lista-plantillas-cuenta" className="flex flex-col gap-2.5">
          {copias.map((copia) => {
            const etiqueta = ETIQUETA[copia.estado];
            const marca = nombreDeMarca(copia.marca);
            return (
              <li
                key={copia.id}
                data-testid={`plantilla-cuenta-${copia.maestra_codigo}`}
                className="flex flex-col gap-2 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-semibold">{copia.maestra_codigo}</span>
                    <span className="text-[var(--ui-texto-suave)]">
                      · basada en la versión {copia.maestra_version} de la maestra
                    </span>
                    <span
                      data-testid={etiqueta.id}
                      className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${etiqueta.clase}`}
                    >
                      {etiqueta.texto}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      data-testid={`boton-comparar-${copia.maestra_codigo}`}
                      aria-label={`Comparar ${copia.maestra_codigo} con la maestra`}
                      onClick={(e) => void comparar(copia, e.currentTarget)}
                      className="flex items-center gap-1 rounded-md border border-[var(--ui-borde)] px-2.5 py-1 text-xs font-medium hover:bg-[var(--ui-boton-hover)] cursor-pointer"
                    >
                      <GitCompare className="h-3 w-3" aria-hidden="true" />
                      <span>Comparar con la maestra</span>
                    </button>
                    {copia.estado === "desactualizada" && (
                      <button
                        type="button"
                        data-testid={`boton-aplicar-${copia.maestra_codigo}`}
                        aria-label={`Aplicar la maestra vigente a ${copia.maestra_codigo}`}
                        onClick={() => void aplicar(copia)}
                        disabled={aplicando}
                        className="flex items-center gap-1 rounded-md bg-[var(--ui-primario)] px-2.5 py-1 text-xs font-medium text-[var(--ui-primario-texto)] hover:opacity-90 disabled:opacity-50 cursor-pointer"
                      >
                        <Check className="h-3 w-3" aria-hidden="true" />
                        <span>Aplicar</span>
                      </button>
                    )}
                  </div>
                </div>

                {copia.estado === "desactualizada" && (
                  <p className="text-[11px] text-[var(--ui-texto-suave)]">
                    La maestra tiene una versión más nueva. Compárala antes de aplicarla; no se aplica sola.
                  </p>
                )}
                {copia.estado === "retirada" && (
                  <p className="text-[11px] text-[var(--ui-texto-suave)]">
                    La maestra ya no se publica. Esta copia queda solo para consulta.
                  </p>
                )}
                {marca && <p className="text-[11px] text-[var(--ui-texto-suave)]">Marca de la cuenta: {marca}</p>}
              </li>
            );
          })}
        </ul>
      )}

      {copiaDiff && (
        <ModalDiffMaestra
          abierto
          cerrar={cerrarComparacion}
          codigo={copiaDiff.maestra_codigo}
          versionMaestra={diff?.maestra_vigente ?? ""}
          cambios={diff?.cambios ?? []}
          cargando={cargandoDiff}
          error={errorAplicar}
          alAplicar={() => void aplicar(copiaDiff)}
          aplicando={aplicando}
        />
      )}
    </section>
  );
}
