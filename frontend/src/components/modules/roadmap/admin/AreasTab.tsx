"use client";

import React, { useId, useMemo, useState } from "react";

import { organizacionApi } from "@/lib/roadmap/cliente";
import type { AreaItem } from "@/types/roadmap";
import { aplanar, construirArbol, type NodoArea } from "./arbolAreas";
import { describirError, type ErrorDescrito } from "./errores";
import { BOTON, BOTON_PRIMARIO, BloqueError, CAMPO, ETIQUETA } from "./ui";

export interface AreasTabProps {
  areas: AreaItem[];
  alCambiar: () => Promise<void>;
}

function FilaArea({
  nodo,
  editandoId,
  onEditar,
  onCancelar,
  onGuardar,
  ocupado,
}: {
  nodo: NodoArea;
  editandoId: string | null;
  onEditar: (areaId: string) => void;
  onCancelar: () => void;
  onGuardar: (areaId: string, nombre: string, codigo: string) => void;
  ocupado: boolean;
}) {
  const editando = editandoId === nodo.area.id;
  const id = useId();
  const [nombre, setNombre] = useState(nodo.area.nombre);
  const [codigo, setCodigo] = useState(nodo.area.codigo ?? "");
  const [aviso, setAviso] = useState<string | null>(null);

  return (
    <li data-testid={`area-${nodo.area.id}`} data-nivel={nodo.nivel}>
      <div
        className="flex flex-wrap items-center gap-3 py-1.5 rounded hover:bg-[var(--ui-boton-hover)]"
        style={{ paddingLeft: `${nodo.nivel * 1.25}rem` }}
      >
        {editando ? (
          <form
            aria-label={`Editar ${nodo.area.nombre}`}
            className="flex flex-wrap items-end gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (nombre.trim() === "") {
                setAviso("El nombre del área no puede quedar vacío.");
                return;
              }
              setAviso(null);
              onGuardar(nodo.area.id, nombre.trim(), codigo.trim());
            }}
          >
            <div>
              <label htmlFor={`${id}-nombre`} className={ETIQUETA}>
                Nombre del área
              </label>
              <input id={`${id}-nombre`} className={CAMPO} value={nombre} onChange={(e) => setNombre(e.target.value)} />
            </div>
            <div>
              <label htmlFor={`${id}-codigo`} className={ETIQUETA}>
                Código
              </label>
              <input id={`${id}-codigo`} className={CAMPO} value={codigo} onChange={(e) => setCodigo(e.target.value)} />
            </div>
            <button type="submit" className={BOTON_PRIMARIO} disabled={ocupado}>
              Guardar área
            </button>
            <button type="button" className={BOTON} onClick={onCancelar}>
              Cancelar
            </button>
            {aviso && (
              <p role="alert" className="text-[11px] text-[#ff6b86] basis-full">
                {aviso}
              </p>
            )}
          </form>
        ) : (
          <>
            <span className="text-sm text-zinc-100">{nodo.area.nombre}</span>
            {nodo.area.codigo && <span className="text-[11px] text-[var(--ui-texto-suave)]">{nodo.area.codigo}</span>}
            <button type="button" className={BOTON} onClick={() => onEditar(nodo.area.id)} aria-label={`Editar ${nodo.area.nombre}`}>
              Editar
            </button>
          </>
        )}
      </div>
      {nodo.hijos.length > 0 && (
        <ul>
          {nodo.hijos.map((hijo) => (
            <FilaArea
              key={hijo.area.id}
              nodo={hijo}
              editandoId={editandoId}
              onEditar={onEditar}
              onCancelar={onCancelar}
              onGuardar={onGuardar}
              ocupado={ocupado}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

export function AreasTab({ areas, alCambiar }: AreasTabProps) {
  const id = useId();
  const arbol = useMemo(() => construirArbol(areas), [areas]);
  const opcionesPadre = useMemo(() => aplanar(arbol), [arbol]);

  const [nombre, setNombre] = useState("");
  const [codigo, setCodigo] = useState("");
  const [padre, setPadre] = useState("");
  const [aviso, setAviso] = useState<string | null>(null);
  const [error, setError] = useState<ErrorDescrito | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const [editandoId, setEditandoId] = useState<string | null>(null);

  async function ejecutar(accion: () => Promise<unknown>): Promise<boolean> {
    setError(null);
    setOcupado(true);
    try {
      await accion();
      await alCambiar();
      return true;
    } catch (err: unknown) {
      setError(describirError(err));
      return false;
    } finally {
      setOcupado(false);
    }
  }

  async function crear(evento: React.FormEvent) {
    evento.preventDefault();
    if (nombre.trim() === "") {
      setAviso("Indica el nombre del área.");
      return;
    }
    setAviso(null);
    const ok = await ejecutar(() =>
      organizacionApi.createArea({
        nombre: nombre.trim(),
        codigo: codigo.trim() || null,
        parent_area_id: padre || null,
      }),
    );
    if (ok) {
      setNombre("");
      setCodigo("");
      setPadre("");
    }
  }

  return (
    <div className="space-y-5">
      <form onSubmit={crear} noValidate aria-label="Nueva área" className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-start">
        <div className="sm:col-span-1">
          <label htmlFor={`${id}-nombre`} className={ETIQUETA}>
            Nombre del área
          </label>
          <input id={`${id}-nombre`} className={CAMPO} value={nombre} onChange={(e) => setNombre(e.target.value)} />
        </div>
        <div>
          <label htmlFor={`${id}-codigo`} className={ETIQUETA}>
            Código (opcional)
          </label>
          <input id={`${id}-codigo`} className={CAMPO} value={codigo} onChange={(e) => setCodigo(e.target.value)} />
        </div>
        <div>
          <label htmlFor={`${id}-padre`} className={ETIQUETA}>
            Área superior
          </label>
          <select id={`${id}-padre`} className={CAMPO} value={padre} onChange={(e) => setPadre(e.target.value)}>
            <option value="">Ninguna (área principal)</option>
            {opcionesPadre.map((n) => (
              <option key={n.area.id} value={n.area.id}>
                {`${"— ".repeat(n.nivel)}${n.area.nombre}`}
              </option>
            ))}
          </select>
        </div>
        <div className="sm:pt-[1.15rem]">
          <button type="submit" className={BOTON_PRIMARIO} disabled={ocupado}>
            Crear área
          </button>
        </div>
        {aviso && (
          <p role="alert" className="text-[11px] text-[#ff6b86] sm:col-span-4">
            {aviso}
          </p>
        )}
      </form>

      {error && <BloqueError error={error} testId="error-areas" />}

      {arbol.length === 0 ? (
        <p role="status" className="text-xs text-zinc-400">
          Todavía no hay áreas. Crea la primera para poder acotar roles a un área.
        </p>
      ) : (
        <ul aria-label="Áreas de la organización" className="text-xs">
          {arbol.map((nodo) => (
            <FilaArea
              key={nodo.area.id}
              nodo={nodo}
              editandoId={editandoId}
              onEditar={(areaId) => setEditandoId(areaId)}
              onCancelar={() => setEditandoId(null)}
              onGuardar={async (areaId, n, c) => {
                const ok = await ejecutar(() => organizacionApi.updateArea(areaId, { nombre: n, codigo: c || null }));
                if (ok) setEditandoId(null);
              }}
              ocupado={ocupado}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
