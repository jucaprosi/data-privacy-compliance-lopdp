"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  Building2,
  ChevronDown,
  ChevronRight,
  Crown,
  Edit2,
  Lock,
  Plus,
  UserCheck,
  UserPlus,
} from "lucide-react";

import type { AreaItem, UserItem } from "@/types/roadmap";
import {
  ETIQUETAS_NIVEL,
  ETIQUETAS_TIPO_CARGO,
  estructuraApi,
  type AreaEstructuraNodo,
  type CargoOrganico,
  type InformeCoberturaResponse,
  type NivelAreaEstructura,
  type TipoCargoEstructura,
} from "./estructura";
import { describirError, type ErrorDescrito } from "./errores";
import { BOTON, BOTON_PRIMARIO, BloqueError, CAMPO, ETIQUETA } from "./ui";

export interface EstructuraTabProps {
  arbol: AreaEstructuraNodo[];
  cobertura: InformeCoberturaResponse | null;
  areas: AreaItem[];
  usuarios: UserItem[];
  puedeEditar: boolean;
  alCambiar: () => Promise<void>;
  alIrASolicitudRM10?: () => void;
}

const NIVELES: NivelAreaEstructura[] = ["alta_direccion", "direccion", "jefatura", "unidad"];
const TIPOS_CARGO: TipoCargoEstructura[] = [
  "otro",
  "delegado_proteccion_datos",
  "oficial_cumplimiento",
  "oficial_seguridad_informacion",
  "implementador_proteccion_datos",
  "miembro_administracion_o_control",
  "apoderado_especial_extranjero",
  "nivel_superior_sector_publico",
];

export function EstructuraTab({
  arbol,
  cobertura,
  areas,
  usuarios,
  puedeEditar,
  alCambiar,
  alIrASolicitudRM10,
}: EstructuraTabProps) {
  const [errorAccion, setErrorAccion] = useState<ErrorDescrito | null>(null);
  const [ocupado, setOcupado] = useState(false);

  // Modales / Formularios
  const [mostrarCrearArea, setMostrarCrearArea] = useState(false);
  const [areaParaEditar, setAreaParaEditar] = useState<AreaEstructuraNodo | null>(null);
  const [areaParaNuevoCargo, setAreaParaNuevoCargo] = useState<AreaEstructuraNodo | null>(null);
  const [cargoParaEditar, setCargoParaEditar] = useState<CargoOrganico | null>(null);
  const [cargoParaTitular, setCargoParaTitular] = useState<CargoOrganico | null>(null);

  // Estados locales para formularios
  const [nombreArea, setNombreArea] = useState("");
  const [codigoArea, setCodigoArea] = useState("");
  const [nivelArea, setNivelArea] = useState<NivelAreaEstructura>("unidad");
  const [padreAreaId, setPadreAreaId] = useState<string>("");

  const [nombreCargo, setNombreCargo] = useState("");
  const [tipoCargo, setTipoCargo] = useState<TipoCargoEstructura>("otro");
  const [esJefaturaCargo, setEsJefaturaCargo] = useState(false);
  const [reportaACargoId, setReportaACargoId] = useState<string>("");
  const [titularCargoId, setTitularCargoId] = useState<string>("");

  // Recolectar todos los cargos del árbol para el selector "reporta_a"
  function recolectarCargos(nodos: AreaEstructuraNodo[]): CargoOrganico[] {
    const res: CargoOrganico[] = [];
    function recorrer(lista: AreaEstructuraNodo[]) {
      for (const nodo of lista) {
        if (nodo.cargos) res.push(...nodo.cargos);
        if (nodo.subareas) recorrer(nodo.subareas);
      }
    }
    recorrer(nodos);
    return res;
  }

  const todosLosCargos = recolectarCargos(arbol);

  function abrirCrearArea() {
    setNombreArea("");
    setCodigoArea("");
    setNivelArea("unidad");
    setPadreAreaId("");
    setErrorAccion(null);
    setMostrarCrearArea(true);
  }

  function abrirEditarArea(nodo: AreaEstructuraNodo) {
    setAreaParaEditar(nodo);
    setNombreArea(nodo.nombre);
    setCodigoArea(nodo.codigo ?? "");
    setNivelArea(nodo.nivel);
    setPadreAreaId(nodo.parent_area_id ?? "");
    setErrorAccion(null);
  }

  function abrirCrearCargo(nodo: AreaEstructuraNodo) {
    setAreaParaNuevoCargo(nodo);
    setNombreCargo("");
    setTipoCargo("otro");
    setEsJefaturaCargo(false);
    setReportaACargoId("");
    setTitularCargoId("");
    setErrorAccion(null);
  }

  function abrirEditarCargo(c: CargoOrganico) {
    setCargoParaEditar(c);
    setNombreCargo(c.nombre);
    setTipoCargo(c.tipo_cargo);
    setEsJefaturaCargo(c.es_jefatura);
    setReportaACargoId(c.reporta_a_cargo_id ?? "");
    setTitularCargoId(c.titular_user_id ?? "");
    setErrorAccion(null);
  }

  function abrirAsignarTitular(c: CargoOrganico) {
    setCargoParaTitular(c);
    setTitularCargoId(c.titular_user_id ?? "");
    setErrorAccion(null);
  }

  async function guardarCrearArea(e: React.FormEvent) {
    e.preventDefault();
    if (nombreArea.trim() === "") return;
    setOcupado(true);
    setErrorAccion(null);
    try {
      await estructuraApi.crearArea({
        nombre: nombreArea.trim(),
        codigo: codigoArea.trim() || null,
        nivel: nivelArea,
        parent_area_id: nivelArea === "alta_direccion" ? null : padreAreaId || null,
      });
      setMostrarCrearArea(false);
      await alCambiar();
    } catch (err) {
      setErrorAccion(describirError(err));
    } finally {
      setOcupado(false);
    }
  }

  async function guardarEditarArea(e: React.FormEvent) {
    e.preventDefault();
    if (!areaParaEditar || nombreArea.trim() === "") return;
    setOcupado(true);
    setErrorAccion(null);
    try {
      await estructuraApi.editarArea(areaParaEditar.id, {
        nombre: nombreArea.trim(),
        codigo: codigoArea.trim() || null,
        nivel: nivelArea,
        parent_area_id: nivelArea === "alta_direccion" ? null : padreAreaId || null,
      });
      setAreaParaEditar(null);
      await alCambiar();
    } catch (err) {
      setErrorAccion(describirError(err));
    } finally {
      setOcupado(false);
    }
  }

  async function guardarCrearCargo(e: React.FormEvent) {
    e.preventDefault();
    if (!areaParaNuevoCargo || nombreCargo.trim() === "") return;
    setOcupado(true);
    setErrorAccion(null);
    try {
      await estructuraApi.crearCargo({
        area_id: areaParaNuevoCargo.id,
        nombre: nombreCargo.trim(),
        tipo_cargo: tipoCargo,
        es_jefatura: esJefaturaCargo,
        reporta_a_cargo_id: reportaACargoId || null,
        titular_user_id: titularCargoId || null,
      });
      setAreaParaNuevoCargo(null);
      await alCambiar();
    } catch (err) {
      setErrorAccion(describirError(err));
    } finally {
      setOcupado(false);
    }
  }

  async function guardarEditarCargo(e: React.FormEvent) {
    e.preventDefault();
    if (!cargoParaEditar || nombreCargo.trim() === "") return;
    setOcupado(true);
    setErrorAccion(null);
    try {
      await estructuraApi.editarCargo(cargoParaEditar.id, {
        nombre: nombreCargo.trim(),
        tipo_cargo: tipoCargo,
        es_jefatura: esJefaturaCargo,
        reporta_a_cargo_id: reportaACargoId || null,
        titular_user_id: titularCargoId || null,
      });
      setCargoParaEditar(null);
      await alCambiar();
    } catch (err) {
      setErrorAccion(describirError(err));
    } finally {
      setOcupado(false);
    }
  }

  async function guardarAsignarTitular(e: React.FormEvent) {
    e.preventDefault();
    if (!cargoParaTitular) return;
    setOcupado(true);
    setErrorAccion(null);
    try {
      await estructuraApi.asignarTitular(cargoParaTitular.id, titularCargoId || null);
      setCargoParaTitular(null);
      await alCambiar();
    } catch (err) {
      setErrorAccion(describirError(err));
    } finally {
      setOcupado(false);
    }
  }

  async function removerTitular(cargoId: string) {
    setOcupado(true);
    setErrorAccion(null);
    try {
      await estructuraApi.asignarTitular(cargoId, null);
      await alCambiar();
    } catch (err) {
      setErrorAccion(describirError(err));
    } finally {
      setOcupado(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Encabezado y resumen */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-white">Estructura Orgánica</h3>
          <p className="text-[11px] text-zinc-400 mt-0.5">
            Árbol de unidades, líneas de reporte, jefaturas y estado de titulares o vacantes.
          </p>
        </div>
        {puedeEditar ? (
          <button
            type="button"
            className={BOTON_PRIMARIO}
            onClick={abrirCrearArea}
            disabled={ocupado}
          >
            <Plus className="w-3.5 h-3.5" aria-hidden="true" />
            Nueva unidad
          </button>
        ) : (
          <div data-testid="aviso-solo-lectura" className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#ffb300]/10 border border-[#ffb300]/30 text-[11px] text-[#ffd166]">
            <Lock className="w-3.5 h-3.5" aria-hidden="true" />
            Modo solo lectura (auditoría)
          </div>
        )}
      </div>

      {errorAccion && <BloqueError error={errorAccion} testId="error-accion-estructura" />}

      {/* Alerta de responsables por designar / informe de cobertura */}
      {cobertura && (
        <section aria-label="Informe de cobertura de estructura" className="space-y-3">
          {cobertura.responsables_por_designar.length > 0 && (
            <div
              role="region"
              aria-label="Responsables por designar"
              className="p-3.5 rounded-lg bg-[#3892f3]/10 border border-[#3892f3]/40 text-xs space-y-2"
            >
              <div className="flex items-center gap-2 text-white font-semibold">
                <UserCheck className="w-4 h-4 text-[#3892f3]" aria-hidden="true" />
                <h4>Responsables por designar ({cobertura.responsables_por_designar.length})</h4>
              </div>
              <p className="text-zinc-300 text-[11px]">
                Titulares de jefatura identificados que aún no cuentan con nombramiento de rol formal en su área:
              </p>
              <ul aria-label="Lista de responsables por designar" className="space-y-1.5 pt-1">
                {cobertura.responsables_por_designar.map((item) => (
                  <li
                    key={`${item.area_id}-${item.cargo_id}`}
                    data-testid={`responsable-por-designar-${item.area_id}`}
                    className="flex flex-wrap items-center justify-between gap-2 p-2 rounded bg-[var(--ui-superficie)] border border-[var(--ui-borde)]"
                  >
                    <div>
                      <span className="font-medium text-white">{item.candidato_nombre ?? item.candidato_email}</span>
                      <span className="text-zinc-400 text-[11px]"> · Cargo: {item.nombre_cargo}</span>
                      <span className="text-[var(--ui-texto-suave)] text-[11px]"> ({item.nombre_area})</span>
                    </div>
                    {alIrASolicitudRM10 ? (
                      <button
                        type="button"
                        onClick={alIrASolicitudRM10}
                        className={BOTON}
                      >
                        Iniciar solicitud de alta
                      </button>
                    ) : (
                      <span className="text-[11px] text-zinc-400 italic">
                        Acción de alta disponible con el módulo de solicitudes
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Jefaturas vacantes o unidades sin jefatura */}
          {(cobertura.jefaturas_vacantes.length > 0 || cobertura.unidades_sin_jefatura.length > 0) && (
            <div
              role="region"
              aria-label="Alertas de cobertura orgánica"
              className="p-3.5 rounded-lg bg-[#ffb300]/10 border border-[#ffb300]/40 text-xs space-y-2"
            >
              <div className="flex items-center gap-2 text-[#ffd166] font-semibold">
                <AlertTriangle className="w-4 h-4 text-[#ffd166]" aria-hidden="true" />
                <h4>Alertas de cobertura ({cobertura.jefaturas_vacantes.length + cobertura.unidades_sin_jefatura.length})</h4>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                {cobertura.jefaturas_vacantes.length > 0 && (
                  <div>
                    <span className="font-semibold text-zinc-300">Jefaturas vacantes:</span>
                    <ul aria-label="Lista de jefaturas vacantes" className="list-disc list-inside mt-0.5 text-zinc-400">
                      {cobertura.jefaturas_vacantes.map((v) => (
                        <li key={v.cargo_id} data-testid={`jefatura-vacante-${v.cargo_id}`}>
                          {v.nombre_cargo} en {v.nombre_area}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {cobertura.unidades_sin_jefatura.length > 0 && (
                  <div>
                    <span className="font-semibold text-zinc-300">Unidades sin jefatura definida:</span>
                    <ul aria-label="Lista de unidades sin jefatura" className="list-disc list-inside mt-0.5 text-zinc-400">
                      {cobertura.unidades_sin_jefatura.map((u) => (
                        <li key={u.area_id} data-testid={`unidad-sin-jefatura-${u.area_id}`}>
                          {u.nombre_area} ({ETIQUETAS_NIVEL[u.nivel]})
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </section>
      )}

      {/* Árbol Orgánico */}
      <section aria-label="Árbol orgánico" className="space-y-3">
        {arbol.length === 0 ? (
          <p role="status" className="text-xs text-zinc-400">
            No hay unidades orgánicas registradas todavía. Crea la unidad raíz de «Alta Dirección» para comenzar.
          </p>
        ) : (
          <ul aria-label="Unidades orgánicas" className="space-y-3">
            {arbol.map((nodo) => (
              <NodoAreaItem
                key={nodo.id}
                nodo={nodo}
                nivelProfundidad={0}
                puedeEditar={puedeEditar}
                onEditarArea={abrirEditarArea}
                onCrearCargo={abrirCrearCargo}
                onEditarCargo={abrirEditarCargo}
                onAsignarTitular={abrirAsignarTitular}
                onRemoverTitular={removerTitular}
                ocupado={ocupado}
              />
            ))}
          </ul>
        )}
      </section>

      {/* Formulario / Modal: Crear Unidad */}
      {mostrarCrearArea && (
        <form
          aria-label="Crear unidad orgánica"
          onSubmit={guardarCrearArea}
          className="p-4 rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] space-y-3"
        >
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">Nueva Unidad Orgánica</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="area-crear-nombre" className={ETIQUETA}>
                Nombre de la unidad
              </label>
              <input
                id="area-crear-nombre"
                className={CAMPO}
                value={nombreArea}
                onChange={(e) => setNombreArea(e.target.value)}
                placeholder="Ej. Gerencia General / Dirección de Tecnología"
                required
              />
            </div>
            <div>
              <label htmlFor="area-crear-codigo" className={ETIQUETA}>
                Código (opcional)
              </label>
              <input
                id="area-crear-codigo"
                className={CAMPO}
                value={codigoArea}
                onChange={(e) => setCodigoArea(e.target.value)}
                placeholder="Ej. GG-01 / DTI"
              />
            </div>
            <div>
              <label htmlFor="area-crear-nivel" className={ETIQUETA}>
                Nivel jerárquico
              </label>
              <select
                id="area-crear-nivel"
                className={CAMPO}
                value={nivelArea}
                onChange={(e) => setNivelArea(e.target.value as NivelAreaEstructura)}
              >
                {NIVELES.map((n) => (
                  <option key={n} value={n}>
                    {ETIQUETAS_NIVEL[n]}
                  </option>
                ))}
              </select>
            </div>
            {nivelArea !== "alta_direccion" && (
              <div>
                <label htmlFor="area-crear-padre" className={ETIQUETA}>
                  Unidad superior (padre)
                </label>
                <select
                  id="area-crear-padre"
                  className={CAMPO}
                  value={padreAreaId}
                  onChange={(e) => setPadreAreaId(e.target.value)}
                >
                  <option value="">Sin unidad superior (raíz)</option>
                  {areas.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.nombre} {a.codigo ? `(${a.codigo})` : ""}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <div className="flex gap-2 justify-end pt-2">
            <button
              type="button"
              className={BOTON}
              onClick={() => setMostrarCrearArea(false)}
              disabled={ocupado}
            >
              Cancelar
            </button>
            <button type="submit" className={BOTON_PRIMARIO} disabled={ocupado}>
              Crear unidad
            </button>
          </div>
        </form>
      )}

      {/* Formulario / Modal: Editar Unidad */}
      {areaParaEditar && (
        <form
          aria-label={`Editar unidad ${areaParaEditar.nombre}`}
          onSubmit={guardarEditarArea}
          className="p-4 rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] space-y-3"
        >
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Editar Unidad: {areaParaEditar.nombre}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="area-editar-nombre" className={ETIQUETA}>
                Nombre de la unidad
              </label>
              <input
                id="area-editar-nombre"
                className={CAMPO}
                value={nombreArea}
                onChange={(e) => setNombreArea(e.target.value)}
                required
              />
            </div>
            <div>
              <label htmlFor="area-editar-codigo" className={ETIQUETA}>
                Código
              </label>
              <input
                id="area-editar-codigo"
                className={CAMPO}
                value={codigoArea}
                onChange={(e) => setCodigoArea(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="area-editar-nivel" className={ETIQUETA}>
                Nivel jerárquico
              </label>
              <select
                id="area-editar-nivel"
                className={CAMPO}
                value={nivelArea}
                onChange={(e) => setNivelArea(e.target.value as NivelAreaEstructura)}
              >
                {NIVELES.map((n) => (
                  <option key={n} value={n}>
                    {ETIQUETAS_NIVEL[n]}
                  </option>
                ))}
              </select>
            </div>
            {nivelArea !== "alta_direccion" && (
              <div>
                <label htmlFor="area-editar-padre" className={ETIQUETA}>
                  Unidad superior (padre)
                </label>
                <select
                  id="area-editar-padre"
                  className={CAMPO}
                  value={padreAreaId}
                  onChange={(e) => setPadreAreaId(e.target.value)}
                >
                  <option value="">Sin unidad superior (raíz)</option>
                  {areas
                    .filter((a) => a.id !== areaParaEditar.id)
                    .map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.nombre} {a.codigo ? `(${a.codigo})` : ""}
                      </option>
                    ))}
                </select>
              </div>
            )}
          </div>
          <div className="flex gap-2 justify-end pt-2">
            <button
              type="button"
              className={BOTON}
              onClick={() => setAreaParaEditar(null)}
              disabled={ocupado}
            >
              Cancelar
            </button>
            <button type="submit" className={BOTON_PRIMARIO} disabled={ocupado}>
              Guardar cambios
            </button>
          </div>
        </form>
      )}

      {/* Formulario / Modal: Crear Cargo */}
      {areaParaNuevoCargo && (
        <form
          aria-label={`Crear cargo en ${areaParaNuevoCargo.nombre}`}
          onSubmit={guardarCrearCargo}
          className="p-4 rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] space-y-3"
        >
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Nuevo Cargo en {areaParaNuevoCargo.nombre}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="cargo-crear-nombre" className={ETIQUETA}>
                Nombre del cargo
              </label>
              <input
                id="cargo-crear-nombre"
                className={CAMPO}
                value={nombreCargo}
                onChange={(e) => setNombreCargo(e.target.value)}
                placeholder="Ej. Gerente de Operaciones / Analista de Ciberseguridad"
                required
              />
            </div>
            <div>
              <label htmlFor="cargo-crear-tipo" className={ETIQUETA}>
                Tipo de cargo
              </label>
              <select
                id="cargo-crear-tipo"
                className={CAMPO}
                value={tipoCargo}
                onChange={(e) => setTipoCargo(e.target.value as TipoCargoEstructura)}
              >
                {TIPOS_CARGO.map((t) => (
                  <option key={t} value={t}>
                    {ETIQUETAS_TIPO_CARGO[t]}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="cargo-crear-reporta" className={ETIQUETA}>
                Reporta a (cargo superior)
              </label>
              <select
                id="cargo-crear-reporta"
                className={CAMPO}
                value={reportaACargoId}
                onChange={(e) => setReportaACargoId(e.target.value)}
              >
                <option value="">Sin reporte jerárquico</option>
                {todosLosCargos.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="cargo-crear-titular" className={ETIQUETA}>
                Titular asignado (opcional)
              </label>
              <select
                id="cargo-crear-titular"
                className={CAMPO}
                value={titularCargoId}
                onChange={(e) => setTitularCargoId(e.target.value)}
              >
                <option value="">Vacante (sin titular)</option>
                {usuarios.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.nombre} ({u.email})
                  </option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2 flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="cargo-crear-jefatura"
                checked={esJefaturaCargo}
                onChange={(e) => setEsJefaturaCargo(e.target.checked)}
                className="rounded border-[var(--ui-borde)] bg-[var(--ui-superficie)] text-[#3892f3] focus:ring-[#3892f3]"
              />
              <label htmlFor="cargo-crear-jefatura" className="text-xs text-zinc-300 font-medium">
                Es la jefatura de esta unidad orgánica
              </label>
            </div>
          </div>
          <div className="flex gap-2 justify-end pt-2">
            <button
              type="button"
              className={BOTON}
              onClick={() => setAreaParaNuevoCargo(null)}
              disabled={ocupado}
            >
              Cancelar
            </button>
            <button type="submit" className={BOTON_PRIMARIO} disabled={ocupado}>
              Crear cargo
            </button>
          </div>
        </form>
      )}

      {/* Formulario / Modal: Editar Cargo */}
      {cargoParaEditar && (
        <form
          aria-label={`Editar cargo ${cargoParaEditar.nombre}`}
          onSubmit={guardarEditarCargo}
          className="p-4 rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] space-y-3"
        >
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Editar Cargo: {cargoParaEditar.nombre}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="cargo-editar-nombre" className={ETIQUETA}>
                Nombre del cargo
              </label>
              <input
                id="cargo-editar-nombre"
                className={CAMPO}
                value={nombreCargo}
                onChange={(e) => setNombreCargo(e.target.value)}
                required
              />
            </div>
            <div>
              <label htmlFor="cargo-editar-tipo" className={ETIQUETA}>
                Tipo de cargo
              </label>
              <select
                id="cargo-editar-tipo"
                className={CAMPO}
                value={tipoCargo}
                onChange={(e) => setTipoCargo(e.target.value as TipoCargoEstructura)}
              >
                {TIPOS_CARGO.map((t) => (
                  <option key={t} value={t}>
                    {ETIQUETAS_TIPO_CARGO[t]}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="cargo-editar-reporta" className={ETIQUETA}>
                Reporta a (cargo superior)
              </label>
              <select
                id="cargo-editar-reporta"
                className={CAMPO}
                value={reportaACargoId}
                onChange={(e) => setReportaACargoId(e.target.value)}
              >
                <option value="">Sin reporte jerárquico</option>
                {todosLosCargos
                  .filter((c) => c.id !== cargoParaEditar.id)
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre}
                    </option>
                  ))}
              </select>
            </div>
            <div>
              <label htmlFor="cargo-editar-titular" className={ETIQUETA}>
                Titular asignado
              </label>
              <select
                id="cargo-editar-titular"
                className={CAMPO}
                value={titularCargoId}
                onChange={(e) => setTitularCargoId(e.target.value)}
              >
                <option value="">Vacante (sin titular)</option>
                {usuarios.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.nombre} ({u.email})
                  </option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2 flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="cargo-editar-jefatura"
                checked={esJefaturaCargo}
                onChange={(e) => setEsJefaturaCargo(e.target.checked)}
                className="rounded border-[var(--ui-borde)] bg-[var(--ui-superficie)] text-[#3892f3] focus:ring-[#3892f3]"
              />
              <label htmlFor="cargo-editar-jefatura" className="text-xs text-zinc-300 font-medium">
                Es la jefatura de esta unidad orgánica
              </label>
            </div>
          </div>
          <div className="flex gap-2 justify-end pt-2">
            <button
              type="button"
              className={BOTON}
              onClick={() => setCargoParaEditar(null)}
              disabled={ocupado}
            >
              Cancelar
            </button>
            <button type="submit" className={BOTON_PRIMARIO} disabled={ocupado}>
              Guardar cambios
            </button>
          </div>
        </form>
      )}

      {/* Formulario / Modal: Asignar o Cambiar Titular */}
      {cargoParaTitular && (
        <form
          aria-label={`Asignar titular a ${cargoParaTitular.nombre}`}
          onSubmit={guardarAsignarTitular}
          className="p-4 rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] space-y-3"
        >
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Titular para {cargoParaTitular.nombre}
          </h4>
          <div>
            <label htmlFor="cargo-titular-select" className={ETIQUETA}>
              Seleccionar persona titular
            </label>
            <select
              id="cargo-titular-select"
              className={CAMPO}
              value={titularCargoId}
              onChange={(e) => setTitularCargoId(e.target.value)}
            >
              <option value="">Dejar como vacante</option>
              {usuarios.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nombre} ({u.email})
                </option>
              ))}
            </select>
          </div>
          <div className="flex gap-2 justify-end pt-2">
            <button
              type="button"
              className={BOTON}
              onClick={() => setCargoParaTitular(null)}
              disabled={ocupado}
            >
              Cancelar
            </button>
            <button type="submit" className={BOTON_PRIMARIO} disabled={ocupado}>
              Confirmar titular
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

function NodoAreaItem({
  nodo,
  nivelProfundidad,
  puedeEditar,
  onEditarArea,
  onCrearCargo,
  onEditarCargo,
  onAsignarTitular,
  onRemoverTitular,
  ocupado,
}: {
  nodo: AreaEstructuraNodo;
  nivelProfundidad: number;
  puedeEditar: boolean;
  onEditarArea: (nodo: AreaEstructuraNodo) => void;
  onCrearCargo: (nodo: AreaEstructuraNodo) => void;
  onEditarCargo: (cargo: CargoOrganico) => void;
  onAsignarTitular: (cargo: CargoOrganico) => void;
  onRemoverTitular: (cargoId: string) => void;
  ocupado: boolean;
}) {
  const [colapsado, setColapsado] = useState(false);

  return (
    <li
      data-testid={`area-nodo-${nodo.id}`}
      data-nivel={nodo.nivel}
      className="rounded-lg bg-[var(--ui-superficie)] border border-[var(--ui-borde)] overflow-hidden"
    >
      {/* Cabecera del Nodo Unidad */}
      <div
        className="flex flex-wrap items-center justify-between gap-3 p-3 bg-[#18181d] border-b border-[var(--ui-borde)]"
        style={{ paddingLeft: `${Math.max(0.75, nivelProfundidad * 1.5)}rem` }}
      >
        <div className="flex items-center gap-2 min-w-0">
          {(nodo.subareas.length > 0 || nodo.cargos.length > 0) && (
            <button
              type="button"
              aria-label={colapsado ? `Expandir ${nodo.nombre}` : `Colapsar ${nodo.nombre}`}
              onClick={() => setColapsado(!colapsado)}
              className="text-zinc-400 hover:text-white p-0.5"
            >
              {colapsado ? (
                <ChevronRight className="w-4 h-4" aria-hidden="true" />
              ) : (
                <ChevronDown className="w-4 h-4" aria-hidden="true" />
              )}
            </button>
          )}
          <Building2 className="w-4 h-4 text-[#3892f3] shrink-0" aria-hidden="true" />
          <div className="min-w-0">
            <span className="text-xs font-bold text-white tracking-wide">{nodo.nombre}</span>
            {nodo.codigo && <span className="ml-1.5 text-[11px] text-zinc-400">({nodo.codigo})</span>}
            <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[var(--ui-boton)] text-zinc-300">
              {ETIQUETAS_NIVEL[nodo.nivel]}
            </span>
          </div>
        </div>

        {puedeEditar && (
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              className={BOTON}
              onClick={() => onEditarArea(nodo)}
              disabled={ocupado}
            >
              <Edit2 className="w-3 h-3" aria-hidden="true" />
              Editar unidad
            </button>
            <button
              type="button"
              className={BOTON}
              onClick={() => onCrearCargo(nodo)}
              disabled={ocupado}
            >
              <Plus className="w-3 h-3" aria-hidden="true" />
              Nuevo cargo
            </button>
          </div>
        )}
      </div>

      {!colapsado && (
        <div className="p-3 space-y-3" style={{ paddingLeft: `${Math.max(1, nivelProfundidad * 1.5)}rem` }}>
          {/* Cargos del Área */}
          {nodo.cargos.length === 0 ? (
            <p className="text-[11px] text-[var(--ui-texto-suave)] italic">Sin cargos orgánicos registrados en esta unidad.</p>
          ) : (
            <div className="space-y-1.5">
              <span className="text-[10px] uppercase font-bold tracking-wider text-zinc-400">Cargos Orgánicos:</span>
              <ul aria-label={`Cargos de ${nodo.nombre}`} className="space-y-1.5">
                {nodo.cargos.map((cargo) => (
                  <li
                    key={cargo.id}
                    data-testid={`cargo-${cargo.id}`}
                    className="flex flex-wrap items-center justify-between gap-2 p-2 rounded bg-[var(--ui-campo)] border border-[var(--ui-borde)] text-xs"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      {cargo.es_jefatura && (
                        <span title="Jefatura de unidad" className="inline-flex">
                          <Crown className="w-3.5 h-3.5 text-[#ffd166] shrink-0" aria-hidden="true" />
                        </span>
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-zinc-200">{cargo.nombre}</span>
                          <span className="text-[10px] text-zinc-400 font-mono">
                            [{ETIQUETAS_TIPO_CARGO[cargo.tipo_cargo]}]
                          </span>
                        </div>
                        <div className="text-[11px] text-zinc-400 mt-0.5">
                          {cargo.titular_user_id ? (
                            <span className="text-zinc-300">
                              Titular:{" "}
                              <strong className="text-white">
                                {cargo.titular_nombre ?? cargo.titular_email ?? cargo.titular_user_id}
                              </strong>
                            </span>
                          ) : (
                            <span
                              data-testid={`vacante-${cargo.id}`}
                              className="inline-flex items-center gap-1 font-semibold text-[#ffd166]"
                            >
                              <AlertTriangle className="w-3 h-3" aria-hidden="true" />
                              Vacante
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {puedeEditar && (
                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          className={BOTON}
                          onClick={() => onEditarCargo(cargo)}
                          disabled={ocupado}
                        >
                          Editar
                        </button>
                        {cargo.titular_user_id ? (
                          <>
                            <button
                              type="button"
                              className={BOTON}
                              onClick={() => onAsignarTitular(cargo)}
                              disabled={ocupado}
                            >
                              Cambiar titular
                            </button>
                            <button
                              type="button"
                              className={BOTON}
                              onClick={() => onRemoverTitular(cargo.id)}
                              disabled={ocupado}
                            >
                              Quitar titular
                            </button>
                          </>
                        ) : (
                          <button
                            type="button"
                            className={BOTON}
                            onClick={() => onAsignarTitular(cargo)}
                            disabled={ocupado}
                          >
                            <UserPlus className="w-3 h-3" aria-hidden="true" />
                            Asignar titular
                          </button>
                        )}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Subáreas hijas recursivas */}
          {nodo.subareas.length > 0 && (
            <ul aria-label={`Subáreas de ${nodo.nombre}`} className="space-y-2.5 pt-1">
              {nodo.subareas.map((sub) => (
                <NodoAreaItem
                  key={sub.id}
                  nodo={sub}
                  nivelProfundidad={nivelProfundidad + 1}
                  puedeEditar={puedeEditar}
                  onEditarArea={onEditarArea}
                  onCrearCargo={onCrearCargo}
                  onEditarCargo={onEditarCargo}
                  onAsignarTitular={onAsignarTitular}
                  onRemoverTitular={onRemoverTitular}
                  ocupado={ocupado}
                />
              ))}
            </ul>
          )}
        </div>
      )}
    </li>
  );
}
