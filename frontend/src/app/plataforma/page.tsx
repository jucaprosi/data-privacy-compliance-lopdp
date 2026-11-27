// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

import * as React from "react";
import { Check, Clipboard, Plus, RefreshCw, ShieldAlert, XCircle } from "lucide-react";

import {
  ErrorPlataforma,
  plataformaApi,
  type AltaOrganizacion,
  type OrganizacionCrear,
  type OrganizacionResumen,
} from "@/lib/plataforma";

const VACIO: OrganizacionCrear = {
  nombre_comercial: "",
  razon_social: "",
  ruc_identificacion: "",
  tamano: "micro",
  sector: "",
  email_admin_inicial: "",
};

const etiquetaEstado = (estado: string | null) => {
  const etiquetas: Record<string, string> = {
    pendiente: "Pendiente",
    emitida: "Pendiente",
    aceptada: "Aceptada",
    revocada: "Revocada",
    expirada: "Caducada",
    caducada: "Caducada",
  };
  return estado ? etiquetas[estado] ?? "Sin información" : "Sin invitación";
};

export default function PlataformaPage() {
  const [organizaciones, setOrganizaciones] = React.useState<OrganizacionResumen[]>([]);
  const [formulario, setFormulario] = React.useState<OrganizacionCrear>(VACIO);
  const [alta, setAlta] = React.useState<AltaOrganizacion | null>(null);
  const [cargando, setCargando] = React.useState(true);
  const [guardando, setGuardando] = React.useState(false);
  const [denegado, setDenegado] = React.useState(false);
  const [falloCarga, setFalloCarga] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [copiado, setCopiado] = React.useState(false);
  const [revocandoId, setRevocandoId] = React.useState<string | null>(null);
  const [reemitiendoTenant, setReemitiendoTenant] = React.useState<string | null>(null);

  const cargar = React.useCallback(async () => {
    setCargando(true);
    setError(null);
    setFalloCarga(false);
    try {
      setOrganizaciones(await plataformaApi.listar());
      setDenegado(false);
    } catch (err) {
      if (err instanceof ErrorPlataforma && err.status === 403) setDenegado(true);
      else {
        setFalloCarga(true);
        setError(err instanceof Error ? err.message : "No se pudo completar la operación. Inténtalo de nuevo.");
      }
    } finally {
      setCargando(false);
    }
  }, []);

  React.useEffect(() => {
    void cargar();
  }, [cargar]);

  async function crear(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setGuardando(true);
    setError(null);
    try {
      const creada = await plataformaApi.crear(formulario);
      setAlta(creada);
      setFormulario(VACIO);
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la organización.");
    } finally {
      setGuardando(false);
    }
  }

  async function copiarCodigo() {
    if (!alta) return;
    await navigator.clipboard.writeText(alta.codigo_invitacion);
    setCopiado(true);
  }

  async function revocar() {
    if (!alta) return;
    setError(null);
    try {
      await plataformaApi.revocar(alta.invitacion_id);
      setAlta(null);
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo revocar la invitación.");
    }
  }

  async function revocarDesdeListado(organizacion: OrganizacionResumen) {
    if (!organizacion.invitacion_id) return;
    const confirmada = window.confirm(
      `¿Revocar la invitación pendiente de ${organizacion.nombre_comercial}?`,
    );
    if (!confirmada) return;
    setError(null);
    setRevocandoId(organizacion.invitacion_id);
    try {
      await plataformaApi.revocar(organizacion.invitacion_id);
      setOrganizaciones((actuales) =>
        actuales.map((item) =>
          item.id === organizacion.id ? { ...item, invitacion_estado: "revocada" } : item,
        ),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo revocar la invitación.");
    } finally {
      setRevocandoId(null);
    }
  }

  async function reemitir(organizacion: OrganizacionResumen) {
    setError(null);
    setReemitiendoTenant(organizacion.id);
    try {
      const nueva = await plataformaApi.reemitir(organizacion.id);
      setAlta(nueva);
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo reemitir la invitación.");
    } finally {
      setReemitiendoTenant(null);
    }
  }

  if (denegado) {
    return (
      <main className="min-h-screen bg-[var(--background)] px-6 py-16 text-[var(--foreground)]">
        <section className="mx-auto max-w-xl rounded-2xl border border-[color:var(--ui-error-borde)] bg-[var(--ui-superficie)] p-8 text-center">
          <ShieldAlert className="mx-auto h-10 w-10 text-[var(--ui-error-texto)]" aria-hidden="true" />
          <h1 className="mt-4 text-2xl font-semibold">Acceso denegado</h1>
          <p className="mt-2 text-sm text-[var(--ui-texto-suave)]">Esta sección está reservada para operadores de la plataforma.</p>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[var(--background)] px-5 py-8 text-[var(--foreground)]">
      <div className="mx-auto max-w-6xl space-y-8">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--ui-texto-suave)]">Administración global</p>
            <h1 className="mt-2 text-3xl font-semibold">Organizaciones</h1>
            <p className="mt-2 text-sm text-[var(--ui-texto-suave)]">Altas e invitaciones iniciales sin acceso a los datos de cada organización.</p>
          </div>
          <button onClick={() => void cargar()} className="inline-flex items-center gap-2 rounded-lg border border-[color:var(--ui-borde-control)] px-3 py-2 text-sm hover:bg-[var(--ui-boton-hover)]">
            <RefreshCw className="h-4 w-4" aria-hidden="true" /> Actualizar
          </button>
        </header>

        {error && <p role="alert" className="rounded-lg border border-[color:var(--ui-error-borde)] bg-[var(--ui-error-fondo)] px-4 py-3 text-sm text-[var(--ui-error-texto)]">{error}</p>}

        {alta && (
          <section aria-labelledby="codigo-titulo" className="rounded-2xl border border-[color:var(--ui-aviso-borde)] bg-[var(--ui-aviso-fondo)] p-5">
            <h2 id="codigo-titulo" className="text-lg font-semibold text-[var(--ui-aviso-titulo)]">Código de invitación — visible una sola vez</h2>
            <p className="mt-1 text-sm text-[var(--ui-aviso-texto)]">Cópialo ahora y envíalo por un canal seguro. No se podrá volver a consultar después de salir o recargar.</p>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <code data-testid="codigo-invitacion" className="max-w-full break-all rounded-lg bg-[var(--ui-superficie-2)] px-4 py-3 text-sm text-[var(--ui-aviso-texto)]">{alta.codigo_invitacion}</code>
              <button onClick={() => void copiarCodigo()} className="inline-flex items-center gap-2 rounded-lg bg-[var(--ui-primario)] px-3 py-2 text-sm font-semibold text-[var(--ui-primario-texto)]">
                {copiado ? <Check className="h-4 w-4" /> : <Clipboard className="h-4 w-4" />} {copiado ? "Copiado" : "Copiar código"}
              </button>
              <button onClick={() => void revocar()} className="inline-flex items-center gap-2 rounded-lg border border-[color:var(--ui-peligro-texto)] px-3 py-2 text-sm text-[var(--ui-peligro-texto)]">
                <XCircle className="h-4 w-4" /> Revocar invitación
              </button>
            </div>
          </section>
        )}

        <section className="grid gap-6 lg:grid-cols-[360px_1fr]">
          <form onSubmit={crear} aria-label="Crear organización" className="space-y-4 rounded-2xl border border-[color:var(--ui-borde)] bg-[var(--ui-superficie)] p-5">
            <h2 className="flex items-center gap-2 text-lg font-semibold"><Plus className="h-5 w-5 text-[var(--ui-texto-suave)]" /> Nueva organización</h2>
            {([
              ["Nombre comercial", "nombre_comercial", "Empresa Ejemplo"],
              ["Razón social", "razon_social", "Empresa Ejemplo S.A."],
              ["RUC o identificación", "ruc_identificacion", "0999999999001"],
              ["Sector", "sector", "Servicios profesionales"],
              ["Correo del administrador inicial", "email_admin_inicial", "admin@empresa.ec"],
            ] as const).map(([etiqueta, campo, ejemplo]) => (
              <label key={campo} className="block text-sm text-[var(--foreground)]">{etiqueta}
                <input required value={formulario[campo]} onChange={(e) => setFormulario({ ...formulario, [campo]: e.target.value })} placeholder={ejemplo} className="mt-1 w-full rounded-lg border border-[color:var(--ui-borde-control)] bg-[var(--ui-campo)] px-3 py-2 text-[var(--foreground)] outline-none focus:border-[color:var(--ui-primario)]" />
              </label>
            ))}
            <label className="block text-sm text-[var(--foreground)]">Tamaño
              <select value={formulario.tamano} onChange={(e) => setFormulario({ ...formulario, tamano: e.target.value as OrganizacionCrear["tamano"] })} className="mt-1 w-full rounded-lg border border-[color:var(--ui-borde-control)] bg-[var(--ui-campo)] px-3 py-2">
                <option value="micro">Microempresa</option><option value="pequena">Pequeña</option><option value="mediana">Mediana</option><option value="corporativo">Corporativo</option>
              </select>
            </label>
            <button disabled={guardando} className="w-full rounded-lg bg-[var(--ui-primario)] px-4 py-2.5 text-sm font-semibold text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] disabled:opacity-50">{guardando ? "Creando…" : "Crear y emitir invitación"}</button>
          </form>

          <section aria-labelledby="listado-titulo" className="overflow-hidden rounded-2xl border border-[color:var(--ui-borde)] bg-[var(--ui-superficie)]">
            <h2 id="listado-titulo" className="border-b border-[color:var(--ui-borde)] px-5 py-4 text-lg font-semibold">Organizaciones registradas</h2>
            {cargando ? <p role="status" className="p-6 text-sm text-[var(--ui-texto-suave)]">Cargando organizaciones…</p> : falloCarga ? <div className="p-6"><button onClick={() => void cargar()} className="rounded-lg border border-[color:var(--ui-borde-control)] px-3 py-2 text-sm hover:bg-[var(--ui-boton-hover)]">Reintentar</button></div> : organizaciones.length === 0 ? <p className="p-6 text-sm text-[var(--ui-texto-suave)]">Todavía no hay organizaciones.</p> : (
              <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-[var(--ui-superficie-2)] text-xs uppercase text-[var(--ui-texto-suave)]"><tr><th className="p-3">Organización</th><th className="p-3">Identificación</th><th className="p-3">Alta</th><th className="p-3">Administrador</th><th className="p-3">Invitación</th></tr></thead><tbody>
                {organizaciones.map((org) => <tr key={org.id} data-testid={`organizacion-${org.id}`} className="border-t border-[color:var(--ui-borde)]"><td className="p-3"><strong className="block text-[var(--foreground)]">{org.nombre_comercial}</strong><span className="text-[var(--ui-texto-suave)]">{org.razon_social}</span></td><td className="p-3 text-[var(--foreground)]">{org.ruc_identificacion}</td><td className="p-3 text-[var(--foreground)]">{org.created_at ? new Date(org.created_at).toLocaleDateString("es-EC") : "Sin fecha"}<span className="block text-xs text-[var(--ui-texto-suave)]">{org.activo === false ? "Inactiva" : "Activa"}</span></td><td className="p-3 text-[var(--foreground)]">{org.email_admin_inicial ?? "Sin registrar"}</td><td className="p-3"><span className="rounded-full bg-[var(--ui-superficie-2)] px-2 py-1 text-xs">{etiquetaEstado(org.invitacion_estado)}</span>{org.invitacion_estado === "emitida" && org.invitacion_id && <button disabled={revocandoId === org.invitacion_id} onClick={() => void revocarDesdeListado(org)} className="mt-2 block rounded-md border border-[color:var(--ui-peligro-texto)] px-2 py-1 text-xs text-[var(--ui-peligro-texto)] disabled:opacity-50">{revocandoId === org.invitacion_id ? "Revocando…" : "Revocar"}</button>}{["caducada", "revocada"].includes(org.invitacion_estado ?? "") && <button disabled={reemitiendoTenant === org.id} onClick={() => void reemitir(org)} className="mt-2 block rounded-md border border-[color:var(--ui-borde-control)] px-2 py-1 text-xs text-[var(--foreground)] disabled:opacity-50">{reemitiendoTenant === org.id ? "Reemitiendo…" : "Reemitir invitación"}</button>}</td></tr>)}
              </tbody></table></div>
            )}
          </section>
        </section>
      </div>
    </main>
  );
}
