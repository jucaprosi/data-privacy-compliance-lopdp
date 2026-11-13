"use client";
// ¤frontend-ide ¤seguridad
// Pantalla «Papelera» (ORG-20) en Configuración: elementos retirados que se pueden restaurar.
import React, { useCallback, useEffect, useId, useRef, useState } from "react";
import { fechaCorta, papeleraApi, puedeUsarPapelera, type Papelera, type RegistroPapelera } from "./papelera";
import { useRolSedes } from "../sedes/useRolSedes";
import type { OrganizacionRole } from "@/types/roadmap";

const CAMPO =
  "rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-1.5 text-sm text-[var(--ui-texto)]";
const BOTON =
  "rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-1.5 text-sm font-medium text-[var(--ui-texto)] disabled:opacity-50";

export default function PapeleraPantalla() {
  const rol = useRolSedes();
  return (
    <div className="mx-auto max-w-5xl space-y-4 pb-10" data-testid="papelera-organizacion">
      <header>
        <h2 className="text-lg font-semibold text-[var(--ui-texto)]">Papelera</h2>
        <p className="text-sm text-[var(--ui-texto-suave)]">Elementos retirados que puedes restaurar</p>
      </header>
      {rol.fase === "cargando" && <p role="status" className="text-sm">Cargando…</p>}
      {rol.fase === "sin_servidor" && <p className="text-sm">Inicia sesión para ver la papelera de tu organización.</p>}
      {(rol.fase === "sin_rol" || (rol.fase === "lista" && !puedeUsarPapelera(rol.rol))) && (
        <p className="text-sm">No tienes permiso para ver la papelera de esta organización.</p>
      )}
      {rol.fase === "error" && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{rol.mensaje}</p>}
      {rol.fase === "lista" && puedeUsarPapelera(rol.rol) && <Lista rol={rol.rol} />}
    </div>
  );
}

function Lista({ rol }: { rol: OrganizacionRole }) {
  const id = useId();
  const [entidad, setEntidad] = useState("");
  const [datos, setDatos] = useState<Papelera | null>(null);
  const [etiquetas, setEtiquetas] = useState<Papelera["entidades"]>([]);
  const [fallo, setFallo] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);
  const [errorRestaurar, setErrorRestaurar] = useState<string | null>(null);
  const [confirmar, setConfirmar] = useState<RegistroPapelera | null>(null);
  const retorno = useRef<HTMLElement | null>(null);
  const cancelar = useRef<HTMLButtonElement | null>(null);
  const dialogo = useRef<HTMLDivElement | null>(null);

  const cargar = useCallback(async () => {
    try {
      const respuesta = await papeleraApi.listar(rol, entidad || undefined);
      setDatos(respuesta);
      if (!entidad) setEtiquetas(respuesta.entidades);
      setFallo(false);
    } catch {
      setFallo(true);
    }
  }, [rol, entidad]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  useEffect(() => {
    if (confirmar) cancelar.current?.focus();
  }, [confirmar]);

  const cerrar = () => {
    setConfirmar(null);
    retorno.current?.focus();
  };

  const restaurar = async (registro: RegistroPapelera) => {
    try {
      await papeleraApi.restaurar(registro.entidad, registro.id, rol);
      setErrorRestaurar(null);
      setAviso(`${registro.nombre} restaurado.`);
      setConfirmar(null);
      await cargar();
    } catch {
      setAviso(null);
      setErrorRestaurar("No pudimos restaurar el elemento. Inténtalo de nuevo.");
      setConfirmar(null);
    }
  };

  const teclas = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      cerrar();
      return;
    }
    if (e.key !== "Tab" || !dialogo.current) return;
    const focales = Array.from(dialogo.current.querySelectorAll<HTMLElement>("button:not([disabled])"));
    if (focales.length === 0) return;
    const primero = focales[0];
    const ultimo = focales[focales.length - 1];
    if (e.shiftKey && document.activeElement === primero) {
      e.preventDefault();
      ultimo.focus();
    } else if (!e.shiftKey && document.activeElement === ultimo) {
      e.preventDefault();
      primero.focus();
    }
  };

  const etiquetaDe = (clave: string) => etiquetas.find((x) => x.entidad === clave)?.etiqueta ?? clave;
  const registros = datos?.registros ?? [];

  return (
    <section aria-label="Papelera" className="space-y-3">
      {fallo && (
        <div role="alert" className="badge-render-danger flex flex-wrap items-center gap-3 rounded-md px-3 py-2 text-sm">
          <span>No pudimos cargar la papelera. Inténtalo de nuevo.</span>
          <button type="button" className={BOTON} onClick={() => void cargar()}>Volver a cargar</button>
        </div>
      )}
      {errorRestaurar && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{errorRestaurar}</p>}
      {aviso && <p role="status" className="text-sm">{aviso}</p>}
      <div>
        <label htmlFor={`${id}-tipo`} className="mb-1 block text-xs font-semibold text-[var(--ui-texto-suave)]">
          Tipo de elemento
        </label>
        <select id={`${id}-tipo`} className={CAMPO} value={entidad} onChange={(e) => setEntidad(e.target.value)}>
          <option value="">Todos</option>
          {etiquetas.map((e) => (
            <option key={e.entidad} value={e.entidad}>{e.etiqueta}</option>
          ))}
        </select>
      </div>
      {etiquetas.length > 0 && (
        <p className="text-xs text-[var(--ui-texto-suave)]">
          {`Hoy la papelera cubre: ${etiquetas.map((e) => e.etiqueta).join(", ")}. Los demás tipos de elemento se irán sumando.`}
        </p>
      )}
      {datos && !fallo && registros.length === 0 && (
        <p className="text-sm">{entidad ? "No hay elementos retirados de este tipo." : "La papelera está vacía."}</p>
      )}
      {registros.length > 0 && (
        <table className="w-full text-left text-sm max-sm:block">
          <caption className="sr-only">Elementos retirados</caption>
          <thead className="max-sm:sr-only">
            <tr>
              <th scope="col" className="py-1 pr-3">Tipo</th>
              <th scope="col" className="py-1 pr-3">Nombre</th>
              <th scope="col" className="py-1 pr-3">Retirado el</th>
              <th scope="col" className="py-1"><span className="sr-only">Acciones</span></th>
            </tr>
          </thead>
          <tbody className="max-sm:block">
            {registros.map((r) => (
              <tr key={`${r.entidad}-${r.id}`} className="border-t border-[var(--ui-borde)] max-sm:mb-2 max-sm:block max-sm:rounded-md max-sm:border max-sm:p-3">
                <td className="py-2 pr-3 max-sm:block">{etiquetaDe(r.entidad)}</td>
                <td className="py-2 pr-3 font-medium max-sm:block">{r.nombre}</td>
                <td className="py-2 pr-3 max-sm:block">{fechaCorta(r.retirado_en)}</td>
                <td className="py-2 max-sm:block">
                  <button
                    type="button"
                    className={BOTON}
                    onClick={(e) => {
                      retorno.current = e.currentTarget;
                      setConfirmar(r);
                    }}
                  >
                    {`Restaurar ${r.nombre}`}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {confirmar && (
        <div
          ref={dialogo}
          role="dialog"
          aria-modal="true"
          aria-labelledby={`${id}-titulo`}
          onKeyDown={teclas}
          className="space-y-2 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4"
        >
          <h3 id={`${id}-titulo`} className="text-sm font-semibold">{`¿Restaurar ${confirmar.nombre}?`}</h3>
          <p className="text-sm">Vuelve a aparecer donde estaba antes de retirarlo.</p>
          <div className="flex gap-2">
            <button type="button" ref={cancelar} className={BOTON} onClick={cerrar}>Cancelar</button>
            <button type="button" className={BOTON} onClick={() => void restaurar(confirmar)}>Restaurar</button>
          </div>
        </div>
      )}
    </section>
  );
}
