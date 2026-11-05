"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Vista de plantillas de la cuenta profesional (BIB-401).
 *
 * Se monta en la pestaña «Plantillas» (ranura `pestana:plantillas`) desde `vistas/index.ts`.
 * Exclusiva para usuarios con rol 'implementador'.
 * Muestra copias de plantillas con su estado ('vigente', 'desactualizada', 'retirada'),
 * distintivo y botones para «Comparar con la maestra» (diff) y «Aplicar».
 */
import React, { useEffect, useState, useCallback } from "react";
import { GitCompare, Check, RefreshCw, AlertCircle, Briefcase } from "lucide-react";
import type { PropsVistaBiblioteca } from "@/lib/biblioteca/registro";
import {
  esImplementador,
  listarPlantillasCuenta,
  obtenerDiffMaestra,
  aplicarMaestra,
  type PlantillaCuenta,
  type DiffMaestra,
} from "@/lib/biblioteca/plantillasCuenta";
import ModalDiffMaestra from "./ModalDiffMaestra";

export default function VistaPlantillasCuenta() {
  const [esImp, setEsImp] = useState<boolean | null>(null);
  const [copias, setCopias] = useState<PlantillaCuenta[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Estado para el modal de diff
  const [modalAbierto, setModalAbierto] = useState(false);
  const [copiaDiff, setCopiaDiff] = useState<PlantillaCuenta | null>(null);
  const [diffData, setDiffData] = useState<DiffMaestra | null>(null);
  const [cargandoDiff, setCargandoDiff] = useState(false);
  const [aplicando, setAplicando] = useState(false);

  // 1. Verificar si el usuario tiene rol 'implementador'
  useEffect(() => {
    let activo = true;
    esImplementador().then((permitido) => {
      if (activo) setEsImp(permitido);
    });
    return () => {
      activo = false;
    };
  }, []);

  // 2. Cargar copias de plantillas
  const recargar = useCallback(async () => {
    if (esImp !== true) return;
    setCargando(true);
    setError(null);
    try {
      const lista = await listarPlantillasCuenta();
      setCopias(lista);
    } catch (err: unknown) {
      const mensaje = err instanceof Error ? err.message : "Error al cargar las plantillas de cuenta";
      setError(mensaje);
    } finally {
      setCargando(false);
    }
  }, [esImp]);

  useEffect(() => {
    if (esImp === true) {
      recargar();
    }
  }, [esImp, recargar]);

  // Si no es implementador, no se muestra esta sección
  if (esImp === false) {
    return null;
  }

  // Si aún está comprobando rol
  if (esImp === null) {
    return null;
  }

  // Abrir modal de diff
  async function manejarComparar(copia: PlantillaCuenta) {
    setCopiaDiff(copia);
    setCargandoDiff(true);
    setModalAbierto(true);
    try {
      const d = await obtenerDiffMaestra(copia.id);
      setDiffData(d);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al obtener diferencias";
      setError(msg);
      setModalAbierto(false);
    } finally {
      setCargandoDiff(false);
    }
  }

  // Aplicar cambios de la maestra vigente
  async function manejarAplicar(copiaId: string) {
    setAplicando(true);
    try {
      await aplicarMaestra(copiaId);
      setModalAbierto(false);
      await recargar();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al aplicar maestra";
      setError(msg);
    } finally {
      setAplicando(false);
    }
  }

  return (
    <div
      data-testid="vista-plantillas-cuenta"
      className="mt-6 flex flex-col gap-4 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-fondo)] p-4 text-xs"
    >
      {/* Cabecera / Pestaña Mi cuenta */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--ui-borde)] pb-3">
        <div className="flex items-center gap-2">
          <Briefcase className="h-4 w-4 text-[var(--ui-primario)]" />
          <button
            type="button"
            role="tab"
            aria-selected="true"
            data-testid="pestana-mi-cuenta"
            className="font-semibold text-sm cursor-pointer hover:underline"
          >
            Mi cuenta
          </button>
          <span className="text-[var(--ui-texto-suave)] text-xs">
            (Plantillas de la cuenta profesional · Tercera capa)
          </span>
        </div>
        <button
          type="button"
          onClick={recargar}
          disabled={cargando}
          className="flex items-center gap-1 rounded-md border border-[var(--ui-borde)] px-2.5 py-1 text-xs hover:bg-[var(--ui-boton-hover)] cursor-pointer"
        >
          <RefreshCw className={`h-3 w-3 ${cargando ? "animate-spin" : ""}`} />
          <span>Actualizar</span>
        </button>
      </div>

      {error && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-md border border-rose-500/30 bg-rose-500/10 p-2.5 text-xs text-rose-500"
        >
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Listado de copias */}
      {cargando && copias.length === 0 ? (
        <div className="py-6 text-center text-[var(--ui-texto-suave)]">
          Cargando plantillas de tu cuenta profesional...
        </div>
      ) : copias.length === 0 ? (
        <div className="py-6 text-center text-[var(--ui-texto-suave)] italic">
          No tienes copias de plantillas en tu cuenta profesional todavía.
        </div>
      ) : (
        <ul data-testid="lista-plantillas-cuenta" className="flex flex-col gap-2.5">
          {copias.map((copia) => {
            const esDesactualizada = copia.estado === "desactualizada";
            const esVigente = copia.estado === "vigente";

            return (
              <li
                key={copia.id}
                data-testid={`plantilla-cuenta-${copia.maestra_codigo}`}
                className="flex flex-col gap-2 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm">{copia.maestra_codigo}</span>
                    <span className="text-[var(--ui-texto-suave)]">
                      · versión {copia.maestra_version}
                    </span>
                    {/* Distintivo de estado */}
                    {esDesactualizada && (
                      <span
                        data-testid="badge-desactualizada"
                        className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-500"
                      >
                        Desactualizada
                      </span>
                    )}
                    {esVigente && (
                      <span
                        data-testid="badge-vigente"
                        className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-500"
                      >
                        Vigente
                      </span>
                    )}
                    {copia.estado === "retirada" && (
                      <span
                        data-testid="badge-retirada"
                        className="rounded-full border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-2 py-0.5 text-[10px] font-medium text-[var(--ui-texto-suave)]"
                      >
                        Retirada
                      </span>
                    )}
                  </div>

                  {/* Acciones para la copia */}
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      data-testid={`boton-comparar-${copia.maestra_codigo}`}
                      onClick={() => manejarComparar(copia)}
                      className="flex items-center gap-1 rounded-md border border-[var(--ui-borde)] px-2.5 py-1 text-xs font-medium hover:bg-[var(--ui-boton-hover)] cursor-pointer"
                    >
                      <GitCompare className="h-3 w-3" />
                      <span>Comparar con la maestra</span>
                    </button>
                    {esDesactualizada && (
                      <button
                        type="button"
                        data-testid={`boton-aplicar-${copia.maestra_codigo}`}
                        onClick={() => manejarAplicar(copia.id)}
                        disabled={aplicando}
                        className="flex items-center gap-1 rounded-md bg-[var(--ui-primario)] px-2.5 py-1 text-xs font-medium text-[var(--ui-primario-texto)] hover:opacity-90 disabled:opacity-50 cursor-pointer"
                      >
                        <Check className="h-3 w-3" />
                        <span>Aplicar</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Información de marca y criterio */}
                {copia.marca && Object.keys(copia.marca).length > 0 && (
                  <div className="text-[11px] text-[var(--ui-texto-suave)]">
                    Marca: {JSON.stringify(copia.marca)}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {/* Modal de comparación y diff */}
      {copiaDiff && (
        <ModalDiffMaestra
          abierto={modalAbierto}
          cerrar={() => setModalAbierto(false)}
          maestraCodigo={copiaDiff.maestra_codigo}
          maestraVigente={diffData?.maestra_vigente || copiaDiff.maestra_version}
          cambios={cargandoDiff ? ["Cargando diferencias..."] : diffData?.cambios || []}
          alAplicar={() => manejarAplicar(copiaDiff.id)}
          aplicando={aplicando}
        />
      )}
    </div>
  );
}
