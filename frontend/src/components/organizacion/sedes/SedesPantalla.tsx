"use client";
// ¤frontend-ide ¤inventario
// Pantalla de sedes (ORG-18) en el menú Inventario: sede principal y demás sedes de la organización.
import React, { useCallback, useEffect, useId, useState } from "react";
import {
  SEDE_VACIA,
  cuerpoSede,
  puedeEscribirSedes,
  sedesApi,
  validarSede,
  type BorradorSede,
  type Sede,
} from "./sedes";
import { useRolSedes } from "./useRolSedes";
import type { OrganizacionRole } from "@/types/roadmap";

const CAMPO =
  "w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-1.5 text-sm text-[var(--ui-texto)]";
const ETIQUETA = "mb-1 block text-xs font-semibold text-[var(--ui-texto-suave)]";
const BOTON =
  "rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-1.5 text-sm font-medium text-[var(--ui-texto)] disabled:opacity-50";

const mensajeDe = (err: unknown, defecto: string) => (err instanceof Error && err.message ? err.message : defecto);

export default function SedesPantalla() {
  const rol = useRolSedes();
  return (
    <div className="mx-auto max-w-5xl space-y-4 pb-10" data-testid="sedes-organizacion">
      <header>
        <h2 className="text-lg font-semibold text-[var(--ui-texto)]">Sedes de la organización</h2>
        <p className="text-sm text-[var(--ui-texto-suave)]">
          Dónde opera la organización y a quién contactan la autoridad y los titulares. Las áreas se gestionan aparte.
        </p>
      </header>
      {rol.fase === "cargando" && <p role="status" className="text-sm">Cargando…</p>}
      {rol.fase === "sin_servidor" && <p className="text-sm">Inicia sesión para ver las sedes de tu organización.</p>}
      {rol.fase === "sin_rol" && <p className="text-sm">No tienes permiso para ver las sedes de esta organización.</p>}
      {rol.fase === "error" && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{rol.mensaje}</p>}
      {rol.fase === "lista" && <Sedes rol={rol.rol} puedeEditar={puedeEscribirSedes(rol.rol)} />}
    </div>
  );
}

function Sedes({ rol, puedeEditar }: { rol: OrganizacionRole; puedeEditar: boolean }) {
  const id = useId();
  const [sedes, setSedes] = useState<Sede[]>([]);
  const [cargado, setCargado] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [borrador, setBorrador] = useState<BorradorSede>(SEDE_VACIA);
  const [motivo, setMotivo] = useState<string | null>(null);

  const recargar = useCallback(async () => {
    try {
      setSedes(await sedesApi.sedes(rol));
      setError(null);
    } catch (err: unknown) {
      setError(mensajeDe(err, "No pudimos leer las sedes. Inténtalo de nuevo."));
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

  const campo = (k: keyof BorradorSede, v: string | boolean) => setBorrador((b) => ({ ...b, [k]: v }));
  const crear = async () => {
    const m = validarSede(borrador);
    setMotivo(m);
    if (m) return;
    if (await ejecutar(() => sedesApi.crearSede(cuerpoSede(borrador), rol))) setBorrador(SEDE_VACIA);
  };

  const vigentes = sedes.filter((s) => s.retirada_en === null);
  const hayPrincipal = vigentes.some((s) => s.es_principal);

  return (
    <section aria-label="Sedes" className="space-y-3">
      {error && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{error}</p>}
      {!puedeEditar && <p className="text-sm text-[var(--ui-texto-suave)]">Puedes consultar las sedes, pero no modificarlas.</p>}
      {!cargado && <p role="status" className="text-sm">Cargando…</p>}
      {cargado && vigentes.length === 0 && (
        <p className="text-sm">Todavía no hay sedes.{puedeEditar ? " Usa «Agregar sede» para crear la primera." : ""}</p>
      )}
      {vigentes.length > 0 && (
        <ul className="space-y-2">
          {vigentes.map((s) => (
            <li key={s.id} className="flex flex-wrap items-start justify-between gap-2 rounded-md border border-[var(--ui-borde)] p-3">
              <div>
                <p className="text-sm font-semibold">
                  {s.nombre}
                  {s.es_principal && <span className="ml-2 text-xs font-normal">(sede principal)</span>}
                </p>
                <p className="text-xs text-[var(--ui-texto-suave)]">{[s.direccion, s.ciudad, s.provincia].join(", ")}</p>
                {s.contacto_spdp && <p className="text-xs">Contacto para la autoridad: {s.contacto_spdp}</p>}
                {s.contacto_titulares && <p className="text-xs">Contacto para titulares: {s.contacto_titulares}</p>}
                {s.medidas && <p className="text-xs">Medidas físicas: {s.medidas}</p>}
              </div>
              {puedeEditar && (
                <button type="button" className={BOTON} onClick={() => void ejecutar(() => sedesApi.retirarSede(s.id, rol))}>
                  {`Retirar ${s.nombre}`}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {puedeEditar && (
        <form
          noValidate
          aria-label="Agregar sede"
          className="grid gap-3 rounded-md border border-[var(--ui-borde)] p-3 sm:grid-cols-2"
          onSubmit={(e) => {
            e.preventDefault();
            void crear();
          }}
        >
          <div>
            <label htmlFor={`${id}-nombre`} className={ETIQUETA}>Nombre</label>
            <input id={`${id}-nombre`} className={CAMPO} value={borrador.nombre} maxLength={200} onChange={(e) => campo("nombre", e.target.value)} />
          </div>
          <div>
            <label htmlFor={`${id}-direccion`} className={ETIQUETA}>Dirección</label>
            <input id={`${id}-direccion`} className={CAMPO} value={borrador.direccion} maxLength={300} onChange={(e) => campo("direccion", e.target.value)} />
          </div>
          <div>
            <label htmlFor={`${id}-ciudad`} className={ETIQUETA}>Ciudad</label>
            <input id={`${id}-ciudad`} className={CAMPO} value={borrador.ciudad} maxLength={120} onChange={(e) => campo("ciudad", e.target.value)} />
          </div>
          <div>
            <label htmlFor={`${id}-provincia`} className={ETIQUETA}>Provincia</label>
            <input id={`${id}-provincia`} className={CAMPO} value={borrador.provincia} maxLength={120} onChange={(e) => campo("provincia", e.target.value)} />
          </div>
          <div>
            <label htmlFor={`${id}-spdp`} className={ETIQUETA}>Contacto para la autoridad de protección de datos</label>
            <input id={`${id}-spdp`} className={CAMPO} value={borrador.contactoSpdp} maxLength={500} onChange={(e) => campo("contactoSpdp", e.target.value)} />
          </div>
          <div>
            <label htmlFor={`${id}-titulares`} className={ETIQUETA}>Contacto para titulares</label>
            <input id={`${id}-titulares`} className={CAMPO} value={borrador.contactoTitulares} maxLength={500} onChange={(e) => campo("contactoTitulares", e.target.value)} />
          </div>
          <div className="sm:col-span-2">
            <label htmlFor={`${id}-medidas`} className={ETIQUETA}>Medidas físicas de seguridad</label>
            <textarea id={`${id}-medidas`} className={CAMPO} rows={2} value={borrador.medidas} maxLength={2000} onChange={(e) => campo("medidas", e.target.value)} />
          </div>
          <label className="flex items-center gap-2 text-sm sm:col-span-2">
            <input type="checkbox" checked={borrador.esPrincipal} onChange={(e) => campo("esPrincipal", e.target.checked)} />
            Es la sede principal
          </label>
          {borrador.esPrincipal && hayPrincipal && (
            <p className="text-xs text-[var(--ui-texto-suave)] sm:col-span-2">Ya hay una sede principal. Retírala antes de marcar otra.</p>
          )}
          {motivo && <p role="alert" className="text-sm sm:col-span-2">{motivo}</p>}
          <div className="sm:col-span-2">
            <button type="submit" className={BOTON}>Agregar sede</button>
          </div>
        </form>
      )}
    </section>
  );
}
