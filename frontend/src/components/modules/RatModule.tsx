// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

import React, { useState, useEffect, useRef } from "react";
import { FileSpreadsheet, Plus, Database } from "lucide-react";

import { ActividadRAT } from "@/types";
import { ActividadRATConArea, AreaOrganizacion } from "@/types/rat_area";
import { getActividadesRAT, crearActividadRAT } from "@/lib/api";
import { fetchAutenticado } from "@/lib/auth";
import ExportarRat from "@/components/modules/rat/ExportarRat";
import PlantillaSectorial from "@/components/modules/rat/PlantillaSectorial";
import ValidacionesFicha from "@/components/modules/rat/ValidacionesFicha";
// === RAT-07 ===
import Consentimientos from "@/components/modules/rat/Consentimientos";
// === fin RAT-07 ===
import { CONDICIONES_HABILITANTES } from "@/lib/rat/validaciones";

export default function RatModule() {
  const [actividades, setActividades] = useState<ActividadRATConArea[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [fichaAbierta, setFichaAbierta] = useState<ActividadRAT | null>(null);
  // === RAT-07 ===
  const [titularesAbiertos, setTitularesAbiertos] = useState<ActividadRAT | null>(null);
  // === fin RAT-07 ===

  // === RAT-08: Gestión de Áreas ===
  const [areas, setAreas] = useState<AreaOrganizacion[]>([]);
  const [cargandoAreas, setCargandoAreas] = useState(false);
  const [errorCargaAreas, setErrorCargaAreas] = useState<string | null>(null);
  const [errorArea, setErrorArea] = useState<string | null>(null);
  const [errorGuardar, setErrorGuardar] = useState<string | null>(null);
  const [mostrarSelectorRespaldo, setMostrarSelectorRespaldo] = useState(false);
  const areaSelectRef = useRef<HTMLSelectElement | null>(null);

  const formInicial: ActividadRATConArea & { condicion_habilitante?: string | null } = {
    codigo: "RAT-OPER-001",
    nombre: "Facturación Electrónica y Pagos",
    area_responsable: "",
    area_id: null,
    finalidad: "Emisión de comprobantes SRI y cobro de cartera",
    base_legal: "OBLIGACION_LEGAL",
    categorias_titulares: ["CLIENTES", "PROVEEDORES"],
    datos_sensibles: false,
    volumen_titulares_estimado: 12000,
    transferencia_internacional: false,
    requiere_eipd: false,
    es_gran_escala: false,
  };

  const [nueva, setNueva] = useState<ActividadRATConArea & { condicion_habilitante?: string | null }>(formInicial);

  useEffect(() => {
    cargarActividades();
    cargarAreas();
  }, []);

  const cargarAreas = async () => {
    setCargandoAreas(true);
    setErrorCargaAreas(null);
    try {
      const res = await fetchAutenticado("/api/v1/organizacion/areas");
      if (!res.ok) {
        throw new Error("No pudimos cargar las áreas de tu organización.");
      }
      const data = (await res.json()) as AreaOrganizacion[];
      const ordenadas = [...data].sort((a, b) => a.nombre.localeCompare(b.nombre));
      setAreas(ordenadas);
    } catch {
      setErrorCargaAreas("No pudimos cargar las áreas de tu organización.");
    } finally {
      setCargandoAreas(false);
    }
  };

  const cargarActividades = async () => {
    setCargando(true);
    setErrorCarga(null);
    try {
      const data = await getActividadesRAT();
      setActividades(data as ActividadRATConArea[]);
    } catch (error: unknown) {
      setActividades([]);
      setErrorCarga(error instanceof Error ? error.message : "No se pudo cargar el RAT.");
    } finally {
      setCargando(false);
    }
  };

  const abrirModalNuevo = () => {
    setNueva(formInicial);
    setMostrarSelectorRespaldo(false);
    setErrorArea(null);
    setErrorGuardar(null);
    setModalAbierto(true);
    cargarAreas();
  };

  const abrirModalEditar = (act: ActividadRATConArea) => {
    setNueva({
      ...act,
      area_id: act.area_id ?? null,
      area_responsable: act.area_responsable ?? "",
    });
    setMostrarSelectorRespaldo(false);
    setErrorArea(null);
    setErrorGuardar(null);
    setModalAbierto(true);
    cargarAreas();
  };

  const guardarActividad = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorArea(null);
    setErrorGuardar(null);

    // Validación de área
    if (areas.length > 0 && !errorCargaAreas) {
      const exigeSelector = !nueva.area_responsable || mostrarSelectorRespaldo;
      if (exigeSelector && !nueva.area_id) {
        setErrorArea("Elige el área responsable.");
        return;
      }
    } else {
      if (!nueva.area_responsable.trim()) {
        setErrorArea("Elige el área responsable.");
        return;
      }
    }

    try {
      const payload: ActividadRATConArea = { ...nueva };
      const guardada = await crearActividadRAT(payload as ActividadRAT);
      setActividades([...actividades.filter((a) => a.codigo !== guardada.codigo), guardada as ActividadRATConArea]);
      setModalAbierto(false);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      if (errMsg.includes("422") || errMsg.includes("AREA_NO_VALIDA")) {
        setErrorArea("El área elegida ya no está disponible. Elige otra.");
        cargarAreas();
      } else {
        setErrorGuardar("No pudimos guardar el tratamiento. Inténtalo de nuevo.");
      }
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex justify-between items-center pb-4 border-b border-[var(--ui-borde)]">
        <div>
          <h2 className="text-xl font-bold text-[var(--foreground)] flex items-center">
            <FileSpreadsheet className="w-5 h-5 mr-2 text-[var(--ui-exito-texto)]" /> RAT Maestro (Compliance Graph SSOT)
          </h2>
          <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
            Registro unificado de actividades de tratamiento (Art. 41 LOPDP). Fuente única de verdad.
          </p>
        </div>
        <button
          onClick={abrirModalNuevo}
          className="px-3.5 py-2 bg-[var(--ui-primario)] hover:bg-[var(--ui-primario-hover)] text-[var(--ui-primario-texto)] text-xs font-semibold rounded-lg flex items-center shadow-lg transition"
        >
          <Plus className="w-4 h-4 mr-1.5" />
          Nueva Actividad
        </button>
      </div>

      <ExportarRat />

      {/* Plantilla sectorial (RAT-02): solo aparece si hay una para el sector de la organización */}
      <PlantillaSectorial onCargada={cargarActividades} />

      {errorCarga && <p role="alert" className="text-xs">No se pudo cargar el RAT: {errorCarga}</p>}

      {/* Table */}
      <div className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl overflow-hidden">
        <table className="w-full text-left text-xs text-[var(--ui-texto-suave)]">
          <thead className="bg-[var(--ui-superficie-2)] text-[var(--ui-texto-suave)] border-b border-[var(--ui-borde)] font-semibold">
            <tr>
              <th className="p-3">Código</th>
              <th className="p-3">Actividad / Tratamiento</th>
              <th className="p-3">Área</th>
              <th className="p-3">Base Legal</th>
              <th className="p-3 text-center">Titulares Est.</th>
              <th className="p-3 text-center">Datos Sensibles</th>
              <th className="p-3 text-center">Gran Escala</th>
              <th className="p-3 text-center">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--ui-borde)]">
            {cargando ? (
              <tr>
                <td colSpan={8} className="p-6 text-center text-[var(--ui-texto-suave)]">
                  Cargando inventario maestro...
                </td>
              </tr>
            ) : actividades.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-6 text-center text-[var(--ui-texto-suave)]">
                  No hay actividades registradas en el RAT.
                </td>
              </tr>
            ) : (
              actividades.map((act) => (
                <tr key={act.codigo} className="hover:bg-[var(--ui-superficie-2)] transition">
                  <td className="p-3 font-mono text-[var(--ui-texto-suave)] font-bold">{act.codigo}</td>
                  <td className="p-3">
                    <div className="font-semibold text-[var(--foreground)]">{act.nombre}</div>
                    <div className="text-[11px] text-[var(--ui-texto-suave)] line-clamp-1">{act.finalidad}</div>
                  </td>
                  <td className="p-3">{act.area_responsable}</td>
                  <td className="p-3">
                    <span className="bg-[var(--ui-superficie-2)] px-2 py-0.5 rounded text-[11px] font-mono text-[var(--ui-exito-texto)] border border-[var(--ui-borde)]">
                      {act.base_legal}
                    </span>
                  </td>
                  <td className="p-3 text-center font-mono">{act.volumen_titulares_estimado.toLocaleString()}</td>
                  <td className="p-3 text-center">
                    {act.datos_sensibles ? (
                      <span className="text-[var(--ui-error-texto)] font-semibold">SÍ</span>
                    ) : (
                      <span className="text-[var(--ui-texto-suave)]">NO</span>
                    )}
                  </td>
                  <td className="p-3 text-center">
                    {act.es_gran_escala ? (
                      <span className="bg-[var(--ui-error-fondo)] text-[var(--ui-error-texto)] border border-[var(--ui-error-borde)] px-2 py-0.5 rounded text-[10px] font-bold">
                        MTGE
                      </span>
                    ) : (
                      <span className="text-[var(--ui-texto-suave)] text-[11px]">Estándar</span>
                    )}
                  </td>
                  <td className="p-3 text-center space-x-2">
                    <button
                      type="button"
                      onClick={() => abrirModalEditar(act)}
                      aria-label={`Editar ${act.nombre}`}
                      className="underline text-[11px] text-[var(--ui-texto-suave)] hover:text-[var(--foreground)]"
                    >
                      Editar
                    </button>
                    {act.id && (
                      <button
                        type="button"
                        onClick={() => setFichaAbierta(act)}
                        aria-label={`Ver validaciones de ${act.nombre}`}
                        className="underline text-[11px] text-[var(--ui-texto-suave)] hover:text-[var(--foreground)]"
                      >
                        Ver
                      </button>
                    )}
                    {/* === RAT-07 === */}
                    {act.id && (
                      <button
                        type="button"
                        onClick={() => setTitularesAbiertos(act)}
                        aria-label={`Ver titulares de ${act.nombre}`}
                        className="underline text-[11px] text-[var(--ui-exito-texto)] hover:text-[var(--foreground)]"
                      >
                        Titulares
                      </button>
                    )}
                    {/* === fin RAT-07 === */}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* === RAT-07 === */}
      {titularesAbiertos?.id && (
        <div className="rounded-xl border border-[var(--ui-borde)] p-4 space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold">Titulares de {titularesAbiertos.nombre}</h3>
            <button type="button" onClick={() => setTitularesAbiertos(null)} className="underline text-[11px]">
              Cerrar titulares
            </button>
          </div>
          <Consentimientos key={titularesAbiertos.id} ratId={titularesAbiertos.id} nombre={titularesAbiertos.nombre} />
        </div>
      )}
      {/* === fin RAT-07 === */}

      {fichaAbierta?.id && (
        <ValidacionesFicha
          key={fichaAbierta.id}
          ratId={fichaAbierta.id}
          nombre={fichaAbierta.nombre}
          onCerrar={() => setFichaAbierta(null)}
        />
      )}

      {/* Modal Actividad */}
      {modalAbierto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-5 max-w-lg w-full text-[var(--foreground)] shadow-2xl">
            <h3 className="text-sm font-bold text-[var(--ui-exito-texto)] mb-3 flex items-center">
              <Database className="w-4 h-4 mr-2" />
              {nueva.id ? "Editar Actividad de Tratamiento" : "Registrar Nueva Actividad de Tratamiento"}
            </h3>
            <form onSubmit={guardarActividad} className="space-y-3 text-xs">
              <div>
                <label className="block text-[var(--ui-texto-suave)] mb-1">Código Identificador</label>
                <input
                  type="text"
                  value={nueva.codigo}
                  onChange={(e) => setNueva({ ...nueva, codigo: e.target.value })}
                  className="w-full bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] rounded p-2 text-[var(--foreground)]"
                  required
                />
              </div>
              <div>
                <label className="block text-[var(--ui-texto-suave)] mb-1">Nombre del Tratamiento</label>
                <input
                  type="text"
                  value={nueva.nombre}
                  onChange={(e) => setNueva({ ...nueva, nombre: e.target.value })}
                  className="w-full bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] rounded p-2 text-[var(--foreground)]"
                  required
                />
              </div>

              {/* === RAT-08: Sección Área responsable === */}
              <div className="w-full">
                {/* Respaldo (a): Tratamiento existente sin área enlazada pero con áreas en la organización */}
                {nueva.area_responsable && !nueva.area_id && !mostrarSelectorRespaldo && areas.length > 0 && !errorCargaAreas ? (
                  <div className="space-y-1">
                    <span className="block text-[var(--ui-texto-suave)]">Área responsable</span>
                    <p className="text-[var(--foreground)] font-medium">Área registrada: {nueva.area_responsable}</p>
                    <button
                      type="button"
                      onClick={() => {
                        setMostrarSelectorRespaldo(true);
                        setTimeout(() => areaSelectRef.current?.focus(), 50);
                      }}
                      className="text-[var(--ui-exito-texto)] underline hover:text-[var(--foreground)] text-xs inline-block"
                    >
                      Elegir un área de la organización
                    </button>
                  </div>
                ) : areas.length > 0 && !errorCargaAreas ? (
                  /* Selector regular */
                  <div>
                    <label htmlFor="rat-area-select" className="block text-[var(--ui-texto-suave)] mb-1">
                      Área responsable
                    </label>
                    <select
                      id="rat-area-select"
                      ref={areaSelectRef}
                      aria-label="Área responsable"
                      aria-busy={cargandoAreas}
                      aria-disabled={cargandoAreas}
                      aria-invalid={!!errorArea}
                      aria-describedby={errorArea ? "rat-area-error" : "rat-area-ayuda"}
                      disabled={cargandoAreas}
                      value={nueva.area_id ?? ""}
                      onChange={(e) => {
                        const val = e.target.value;
                        const area = areas.find((a) => a.id === val);
                        setNueva({
                          ...nueva,
                          area_id: val || null,
                          area_responsable: area ? area.nombre : "",
                        });
                        setErrorArea(null);
                      }}
                      className="w-full bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] rounded p-2 text-[var(--foreground)]"
                      required
                    >
                      <option value="">{cargandoAreas ? "Cargando las áreas…" : "Elige un área"}</option>
                      {areas.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.nombre}
                        </option>
                      ))}
                    </select>
                    <p id="rat-area-ayuda" className="text-[var(--ui-texto-suave)] text-[11px] mt-1">
                      Las áreas son las de la estructura de tu organización.
                    </p>
                    {mostrarSelectorRespaldo && (
                      <p className="text-[var(--ui-texto-suave)] text-[11px] mt-1">
                        Al guardar, el tratamiento queda enlazado al área que elijas.
                      </p>
                    )}
                    {errorArea && (
                      <p id="rat-area-error" role="alert" className="text-[var(--ui-error-texto)] text-xs mt-1">
                        {errorArea}
                      </p>
                    )}
                  </div>
                ) : (
                  /* Respaldo (b): Organización sin áreas o error al cargar */
                  <div>
                    {errorCargaAreas && (
                      <div role="alert" className="text-[var(--ui-error-texto)] text-xs mb-2 space-y-1">
                        <p>No pudimos cargar las áreas de tu organización.</p>
                        <button
                          type="button"
                          onClick={cargarAreas}
                          className="underline text-[var(--ui-exito-texto)] hover:text-[var(--foreground)]"
                        >
                          Volver a cargar las áreas
                        </button>
                      </div>
                    )}
                    <label htmlFor="rat-area-input" className="block text-[var(--ui-texto-suave)] mb-1">
                      Área responsable
                    </label>
                    <input
                      id="rat-area-input"
                      type="text"
                      aria-label="Área responsable"
                      aria-invalid={!!errorArea}
                      aria-describedby={errorArea ? "rat-area-error" : undefined}
                      value={nueva.area_responsable}
                      onChange={(e) => {
                        setNueva({ ...nueva, area_responsable: e.target.value, area_id: null });
                        setErrorArea(null);
                      }}
                      className="w-full bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] rounded p-2 text-[var(--foreground)]"
                      required
                    />
                    <p role="note" className="text-[var(--ui-texto-suave)] text-[11px] mt-1">
                      Tu organización aún no tiene áreas registradas. Puedes escribir el área a mano por ahora.
                    </p>
                    {errorArea && (
                      <p id="rat-area-error" role="alert" className="text-[var(--ui-error-texto)] text-xs mt-1">
                        {errorArea}
                      </p>
                    )}
                  </div>
                )}
              </div>
              {/* === fin RAT-08 === */}

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[var(--ui-texto-suave)] mb-1">Base de Legitimación</label>
                  <select
                    value={nueva.base_legal}
                    onChange={(e) => setNueva({ ...nueva, base_legal: e.target.value })}
                    className="w-full bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] rounded p-2 text-[var(--foreground)]"
                  >
                    <option value="CONSENTIMIENTO">CONSENTIMIENTO</option>
                    <option value="OBLIGACION_LEGAL">OBLIGACION_LEGAL</option>
                    <option value="CUMPLIMIENTO_CONTRATO">CUMPLIMIENTO_CONTRATO</option>
                    <option value="INTERES_LEGITIMO">INTERES_LEGITIMO</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[var(--ui-texto-suave)] mb-1">Titulares Estimados</label>
                  <input
                    type="number"
                    value={nueva.volumen_titulares_estimado}
                    onChange={(e) => setNueva({ ...nueva, volumen_titulares_estimado: parseInt(e.target.value) || 0 })}
                    className="w-full bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] rounded p-2 text-[var(--foreground)]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[var(--ui-texto-suave)] mb-1">Finalidad Unívoca</label>
                <textarea
                  value={nueva.finalidad}
                  onChange={(e) => setNueva({ ...nueva, finalidad: e.target.value })}
                  className="w-full bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] rounded p-2 text-[var(--foreground)] h-16"
                  required
                />
              </div>

              {nueva.datos_sensibles && (
                <div>
                  <label htmlFor="rat-condicion-habilitante" className="block text-[var(--ui-texto-suave)] mb-1">
                    Condición habilitante (art. 26 LOPDP)
                  </label>
                  <select
                    id="rat-condicion-habilitante"
                    value={nueva.condicion_habilitante ?? ""}
                    onChange={(e) => setNueva({ ...nueva, condicion_habilitante: e.target.value || null })}
                    className="w-full bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] rounded p-2 text-[var(--foreground)]"
                  >
                    <option value="">Sin declarar</option>
                    {CONDICIONES_HABILITANTES.map((c) => (
                      <option key={c.valor} value={c.valor}>
                        {c.etiqueta}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {errorGuardar && (
                <p role="alert" className="text-[var(--ui-error-texto)] text-xs">
                  {errorGuardar}
                </p>
              )}

              <div className="flex items-center justify-between pt-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={nueva.datos_sensibles}
                    onChange={(e) => setNueva({ ...nueva, datos_sensibles: e.target.checked })}
                    className="rounded border-[var(--ui-borde-control)] accent-[var(--ui-primario)]"
                  />
                  <span className="text-[var(--ui-texto-suave)]">Trata datos sensibles</span>
                </label>
                <div className="space-x-2">
                  <button
                    type="button"
                    onClick={() => setModalAbierto(false)}
                    className="px-3 py-1.5 bg-[var(--ui-boton)] text-[var(--foreground)] rounded hover:bg-[var(--ui-boton-hover)]"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] rounded font-semibold hover:bg-[var(--ui-primario-hover)]"
                  >
                    Guardar en RAT
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
