"use client";
// ¤frontend-ide ¤inventario
// Pantalla de clientes por encargo (ORG-18) en el menú Inventario: solo para organizaciones que tratan datos
// por encargo. El servidor decide (409 NO_ES_ENCARGADA); aquí solo se explica, sin mostrar el código.
import React, { useCallback, useEffect, useId, useState } from "react";
import {
  CLIENTE_VACIO,
  cuerpoCliente,
  erroresCliente,
  esNoEsEncargada,
  formatearFecha,
  puedeEscribirSedes,
  sedesApi,
  vigenciaVencida,
  type BorradorCliente,
  type Cliente,
  type ErroresCliente,
} from "./sedes";
import { useRolSedes } from "./useRolSedes";
import type { OrganizacionRole } from "@/types/roadmap";

const CAMPO =
  "w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-1.5 text-sm text-[var(--ui-texto)]";
const ETIQUETA = "mb-1 block text-xs font-semibold text-[var(--ui-texto-suave)]";
const AYUDA = "mt-1 text-xs text-[var(--ui-texto-suave)]";
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
  const [errorLectura, setErrorLectura] = useState<string | null>(null);
  const [errorGuardado, setErrorGuardado] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [borrador, setBorrador] = useState<BorradorCliente>(CLIENTE_VACIO);
  const [errores, setErrores] = useState<ErroresCliente>({});
  const [confirmar, setConfirmar] = useState<Cliente | null>(null);

  const recargar = useCallback(async () => {
    try {
      setClientes(await sedesApi.clientes(rol));
      setNoAplica(false);
      setErrorLectura(null);
    } catch (err: unknown) {
      if (esNoEsEncargada(err)) setNoAplica(true);
      else setErrorLectura(mensajeDe(err, "No pudimos leer los clientes. Inténtalo de nuevo."));
    } finally {
      setCargado(true);
    }
  }, [rol]);

  useEffect(() => {
    void recargar();
  }, [recargar]);

  const ejecutar = async (accion: () => Promise<void>, exito: string): Promise<boolean> => {
    try {
      await accion();
      await recargar();
      setErrorGuardado(null);
      setAviso(exito);
      return true;
    } catch (err: unknown) {
      setAviso(null);
      setErrorGuardado(mensajeDe(err, "No pudimos guardar los cambios. Inténtalo de nuevo."));
      return false;
    }
  };

  const campo = (k: keyof BorradorCliente, v: string) => setBorrador((b) => ({ ...b, [k]: v }));
  const crear = async () => {
    const e = erroresCliente(borrador);
    setErrores(e);
    if (e.razonSocial || e.ruc || e.contrato) return;
    if (await ejecutar(() => sedesApi.crearCliente(cuerpoCliente(borrador), rol), "Cliente agregado.")) setBorrador(CLIENTE_VACIO);
  };
  const retirar = async (cliente: Cliente) => {
    setConfirmar(null);
    await ejecutar(() => sedesApi.retirarCliente(cliente.id, rol), "Cliente retirado.");
  };

  if (!cargado) return <p role="status" className="text-sm">Cargando…</p>;
  if (noAplica) {
    return (
      <p className="text-sm">
        Esta sección es solo para organizaciones que tratan datos por encargo de otras. Tu organización no figura como encargada del
        tratamiento, así que aquí no hay clientes que administrar.
      </p>
    );
  }
  const vigentes = clientes.filter((c) => c.retirado_en === null);
  const marca = (clave: keyof ErroresCliente) =>
    errores[clave] ? { "aria-invalid": true as const, "aria-describedby": `${id}-${clave}-error` } : {};

  return (
    <section aria-label="Clientes" className="space-y-3">
      {errorLectura && (
        <div role="alert" className="badge-render-danger flex flex-wrap items-center gap-3 rounded-md px-3 py-2 text-sm">
          <span>{errorLectura}</span>
          <button type="button" className={BOTON} onClick={() => void recargar()}>Reintentar</button>
        </div>
      )}
      {errorGuardado && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{errorGuardado}</p>}
      {aviso && <p role="status" className="text-sm">{aviso}</p>}
      {!puedeEditar && <p className="text-sm text-[var(--ui-texto-suave)]">Puedes consultar los clientes, pero no modificarlos.</p>}
      {!errorLectura && vigentes.length === 0 && (
        <p className="text-sm">Todavía no hay clientes.{puedeEditar ? " Usa «Agregar cliente» para crear el primero." : ""}</p>
      )}
      {vigentes.length > 0 && (
        <ul className="space-y-2">
          {vigentes.map((c) => {
            const vencida = c.vigente_hasta !== null && vigenciaVencida(c.vigente_hasta);
            return (
              <li key={c.id} className="rounded-md border border-[var(--ui-borde)] p-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold">
                      {c.razon_social} <span className="font-normal text-[var(--ui-texto-suave)]">· RUC {c.ruc}</span>
                    </p>
                    <p className="text-xs text-[var(--ui-texto-suave)]">
                      {[
                        c.contrato_sha256 ? "Contrato registrado" : "Sin contrato",
                        c.vigente_hasta === null
                          ? "Sin fecha de vigencia"
                          : vencida
                            ? `⚠ Vigencia vencida el ${formatearFecha(c.vigente_hasta)}`
                            : `Vigente hasta ${formatearFecha(c.vigente_hasta)}`,
                      ].join(" · ")}
                    </p>
                  </div>
                  {puedeEditar && confirmar?.id !== c.id && (
                    <button type="button" className={BOTON} onClick={() => setConfirmar(c)}>
                      {`Retirar ${c.razon_social}`}
                    </button>
                  )}
                </div>
                {puedeEditar && confirmar?.id === c.id && (
                  <div role="group" aria-label={`Confirmar el retiro de ${c.razon_social}`} className="mt-3 space-y-2 rounded-md border border-[var(--ui-borde)] p-3">
                    <p className="text-sm">{`¿Retirar al cliente ${c.razon_social}? Dejará de aparecer en la lista y quedará en el historial.`}</p>
                    <div className="flex gap-2">
                      <button type="button" className={BOTON} autoFocus onClick={() => setConfirmar(null)}>Cancelar</button>
                      <button type="button" className={BOTON} onClick={() => void retirar(c)}>Retirar</button>
                    </div>
                  </div>
                )}
              </li>
            );
          })}
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
            <input id={`${id}-razon`} className={CAMPO} value={borrador.razonSocial} maxLength={200} onChange={(e) => campo("razonSocial", e.target.value)} {...marca("razonSocial")} />
            {errores.razonSocial && <p id={`${id}-razonSocial-error`} role="alert" className="mt-1 text-sm">{errores.razonSocial}</p>}
          </div>
          <div>
            <label htmlFor={`${id}-ruc`} className={ETIQUETA}>RUC</label>
            <input
              id={`${id}-ruc`}
              inputMode="numeric"
              pattern="[0-9]{13}"
              className={CAMPO}
              value={borrador.ruc}
              maxLength={13}
              onChange={(e) => campo("ruc", e.target.value)}
              {...marca("ruc")}
            />
            {errores.ruc && <p id={`${id}-ruc-error`} role="alert" className="mt-1 text-sm">{errores.ruc}</p>}
          </div>
          <div>
            <label htmlFor={`${id}-contrato`} className={ETIQUETA}>Huella de integridad del contrato (SHA-256, opcional)</label>
            <input
              id={`${id}-contrato`}
              className={CAMPO}
              value={borrador.contratoSha256}
              maxLength={64}
              autoComplete="off"
              onChange={(e) => campo("contratoSha256", e.target.value)}
              aria-describedby={`${id}-contrato-ayuda${errores.contrato ? ` ${id}-contrato-error` : ""}`}
              aria-invalid={errores.contrato ? true : undefined}
            />
            <p id={`${id}-contrato-ayuda`} className={AYUDA}>Si no la tienes, déjala vacía.</p>
            {errores.contrato && <p id={`${id}-contrato-error`} role="alert" className="mt-1 text-sm">{errores.contrato}</p>}
          </div>
          <div>
            <label htmlFor={`${id}-vigencia`} className={ETIQUETA}>Vigente hasta (opcional)</label>
            <input id={`${id}-vigencia`} type="date" className={CAMPO} value={borrador.vigenteHasta} onChange={(e) => campo("vigenteHasta", e.target.value)} />
          </div>
          <div className="sm:col-span-2">
            <button type="submit" className={BOTON}>Agregar cliente</button>
          </div>
        </form>
      )}
    </section>
  );
}
