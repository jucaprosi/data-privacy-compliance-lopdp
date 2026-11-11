"use client";
// ¤frontend-ide ¤inventario
// Pantalla de clientes por encargo (ORG-18) en el menú Inventario: solo para organizaciones que tratan datos
// por encargo. El servidor decide (409 NO_ES_ENCARGADA); aquí solo se explica.
import React, { useCallback, useEffect, useId, useState } from "react";
import {
  CLIENTE_VACIO,
  cuerpoCliente,
  esNoEsEncargada,
  puedeEscribirSedes,
  sedesApi,
  validarCliente,
  type BorradorCliente,
  type Cliente,
} from "./sedes";
import { useRolSedes } from "./useRolSedes";
import type { OrganizacionRole } from "@/types/roadmap";

const CAMPO =
  "w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-1.5 text-sm text-[var(--ui-texto)]";
const ETIQUETA = "mb-1 block text-xs font-semibold text-[var(--ui-texto-suave)]";
const BOTON =
  "rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-1.5 text-sm font-medium text-[var(--ui-texto)] disabled:opacity-50";

const mensajeDe = (err: unknown, defecto: string) => (err instanceof Error && err.message ? err.message : defecto);

export default function ClientesPantalla() {
  const rol = useRolSedes();
  return (
    <div className="mx-auto max-w-5xl space-y-4 pb-10" data-testid="clientes-encargo">
      <header>
        <h2 className="text-lg font-semibold text-[var(--ui-texto)]">Clientes</h2>
        <p className="text-sm text-[var(--ui-texto-suave)]">
          Organizaciones para las que tratas datos personales por encargo, con su contrato y vigencia.
        </p>
      </header>
      {rol.fase === "cargando" && <p role="status" className="text-sm">Cargando…</p>}
      {rol.fase === "sin_servidor" && <p className="text-sm">Inicia sesión para ver los clientes de tu organización.</p>}
      {rol.fase === "sin_rol" && <p className="text-sm">No tienes permiso para ver los clientes de esta organización.</p>}
      {rol.fase === "error" && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{rol.mensaje}</p>}
      {rol.fase === "lista" && <Clientes rol={rol.rol} puedeEditar={puedeEscribirSedes(rol.rol)} />}
    </div>
  );
}

function Clientes({ rol, puedeEditar }: { rol: OrganizacionRole; puedeEditar: boolean }) {
  const id = useId();
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [cargado, setCargado] = useState(false);
  const [noAplica, setNoAplica] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [borrador, setBorrador] = useState<BorradorCliente>(CLIENTE_VACIO);
  const [motivo, setMotivo] = useState<string | null>(null);

  const recargar = useCallback(async () => {
    try {
      setClientes(await sedesApi.clientes(rol));
      setNoAplica(false);
      setError(null);
    } catch (err: unknown) {
      if (esNoEsEncargada(err)) setNoAplica(true);
      else setError(mensajeDe(err, "No pudimos leer los clientes. Inténtalo de nuevo."));
    } finally {
      setCargado(true);
    }
  }, [rol]);

  useEffect(() => {
    void recargar();
  }, [recargar]);

  const ejecutar = async (accion: () => Promise<void>): Promise<boolean> => {
    try {
      await accion();
      await recargar();
      return true;
    } catch (err: unknown) {
      setError(mensajeDe(err, "No pudimos guardar los cambios. Inténtalo de nuevo."));
      return false;
    }
  };

  const campo = (k: keyof BorradorCliente, v: string) => setBorrador((b) => ({ ...b, [k]: v }));
  const crear = async () => {
    const m = validarCliente(borrador);
    setMotivo(m);
    if (m) return;
    if (await ejecutar(() => sedesApi.crearCliente(cuerpoCliente(borrador), rol))) setBorrador(CLIENTE_VACIO);
  };

  if (!cargado) return <p role="status" className="text-sm">Cargando…</p>;
  if (noAplica) {
    return <p className="text-sm">Esta sección es solo para organizaciones que tratan datos por encargo de otras.</p>;
  }
  const vigentes = clientes.filter((c) => c.retirado_en === null);

  return (
    <section aria-label="Clientes" className="space-y-3">
      {error && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{error}</p>}
      {!puedeEditar && <p className="text-sm text-[var(--ui-texto-suave)]">Puedes consultar los clientes, pero no modificarlos.</p>}
      {vigentes.length === 0 ? (
        <p className="text-sm">Todavía no hay clientes.{puedeEditar ? " Usa «Agregar cliente» para crear el primero." : ""}</p>
      ) : (
        <ul className="space-y-2">
          {vigentes.map((c) => (
            <li key={c.id} className="flex flex-wrap items-start justify-between gap-2 rounded-md border border-[var(--ui-borde)] p-3">
              <div>
                <p className="text-sm font-semibold">{c.razon_social} <span className="font-normal text-[var(--ui-texto-suave)]">· RUC {c.ruc}</span></p>
                <p className="text-xs text-[var(--ui-texto-suave)]">
                  {[c.contrato_sha256 ? "Contrato registrado" : "Sin contrato", c.vigente_hasta ? `Vigente hasta ${c.vigente_hasta}` : "Sin fecha de vigencia"].join(" · ")}
                </p>
              </div>
              {puedeEditar && (
                <button type="button" className={BOTON} onClick={() => void ejecutar(() => sedesApi.retirarCliente(c.id, rol))}>
                  {`Retirar ${c.razon_social}`}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {puedeEditar && (
        <form
          noValidate
          aria-label="Agregar cliente"
          className="grid gap-3 rounded-md border border-[var(--ui-borde)] p-3 sm:grid-cols-2"
          onSubmit={(e) => {
            e.preventDefault();
            void crear();
          }}
        >
          <div>
            <label htmlFor={`${id}-razon`} className={ETIQUETA}>Razón social</label>
            <input id={`${id}-razon`} className={CAMPO} value={borrador.razonSocial} maxLength={200} onChange={(e) => campo("razonSocial", e.target.value)} />
          </div>
          <div>
            <label htmlFor={`${id}-ruc`} className={ETIQUETA}>RUC</label>
            <input id={`${id}-ruc`} inputMode="numeric" className={CAMPO} value={borrador.ruc} maxLength={13} onChange={(e) => campo("ruc", e.target.value)} />
          </div>
          <div>
            <label htmlFor={`${id}-contrato`} className={ETIQUETA}>Huella del contrato (opcional)</label>
            <input id={`${id}-contrato`} className={CAMPO} value={borrador.contratoSha256} maxLength={64} autoComplete="off" onChange={(e) => campo("contratoSha256", e.target.value)} />
          </div>
          <div>
            <label htmlFor={`${id}-vigencia`} className={ETIQUETA}>Vigente hasta (opcional)</label>
            <input id={`${id}-vigencia`} type="date" className={CAMPO} value={borrador.vigenteHasta} onChange={(e) => campo("vigenteHasta", e.target.value)} />
          </div>
          {motivo && <p role="alert" className="text-sm sm:col-span-2">{motivo}</p>}
          <div className="sm:col-span-2">
            <button type="submit" className={BOTON}>Agregar cliente</button>
          </div>
        </form>
      )}
    </section>
  );
}
