"use client";

/**
 * Inicio › Tablero de cartera (ORG-15). ¤cartera ¤tablero-dimensiones
 *
 * Una fila por organización donde la persona tiene un rol vigente: sus roles, las cuatro dimensiones
 * como semáforo (tarjetas de `components/tableros/`, FE-24), las brechas críticas, los hallazgos abiertos
 * y las tareas vencidas. Sin cifra única. Elegir una fila entra en esa organización con el cambio de FE-21.
 */
import * as React from "react";
import { leerOrganizacionActiva, leerSesion, type Organizacion } from "@/lib/auth";
import { consultarCartera, type FilaCartera } from "@/lib/cartera/cliente";
import { tarjetasDeFila } from "@/lib/cartera/semaforos";
import TarjetaDimension from "@/components/tableros/TarjetaDimension";
import { useAuditStore } from "@/store/useAuditStore";
import { cambiarDeOrganizacion, resolverCambiosSinGuardar } from "@/store/datosDeTrabajo";

const ETIQUETA_ROL: Record<string, string> = {
  admin_organizacion: "Administrador",
  coordinador: "Coordinador",
  dpo: "DPO",
  implementador: "Implementador",
  responsable_area: "Responsable de área",
};

type Estado =
  | { fase: "cargando" }
  | { fase: "error" }
  | { fase: "listo"; filas: FilaCartera[] };

const aOrganizacion = (f: FilaCartera): Organizacion => ({ tenant_id: f.tenant_id, nombre_comercial: f.nombre, roles: f.roles });

function Contador({ etiqueta, valor, id }: { etiqueta: string; valor: number | null; id: string }) {
  return (
    <div data-testid={id} className="p-3 rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)]">
      <dt className="text-[11px] uppercase tracking-wider font-semibold text-[var(--ui-texto-suave)]">{etiqueta}</dt>
      <dd className="text-base font-bold">{valor === null ? "Sin datos" : valor}</dd>
    </div>
  );
}

function FilaOrganizacion({ fila, activa, onEntrar }: { fila: FilaCartera; activa: boolean; onEntrar: (f: FilaCartera) => void }) {
  const tarjetas = tarjetasDeFila(fila);
  const sinDatos = fila.error === "SIN_DATOS";
  return (
    <li data-testid={`fila-${fila.tenant_id}`} className="space-y-3 p-4 rounded-xl border border-[var(--ui-borde)]">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-bold">{fila.nombre}</h3>
          <p className="text-xs text-[var(--ui-texto-suave)]">{fila.roles.map((r) => ETIQUETA_ROL[r] ?? r).join(", ")}</p>
        </div>
        {activa ? (
          <span className="badge-render-success text-[10px] px-2 py-0.5 rounded font-semibold">Organización actual</span>
        ) : (
          <button
            type="button"
            onClick={() => onEntrar(fila)}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--ui-borde)] cursor-pointer"
          >
            Entrar en {fila.nombre}
          </button>
        )}
      </div>
      {sinDatos && (
        <p role="status" className="badge-render-warning p-2 rounded-lg text-xs">
          No se pudieron calcular los indicadores de esta organización. Inténtalo de nuevo más tarde.
        </p>
      )}
      {!sinDatos && tarjetas === null && (
        <p className="text-xs text-[var(--ui-texto-suave)]">Esta organización aún no tiene un diagnóstico sellado. Los indicadores aparecerán cuando el DPO selle el diagnóstico.</p>
      )}
      {tarjetas && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          {tarjetas.map((t) => (
            <TarjetaDimension key={t.id} tarjeta={t} />
          ))}
        </div>
      )}
      {!sinDatos && (
        <dl className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Contador id="brechas-criticas" etiqueta="Brechas críticas" valor={fila.diagnostico ? fila.diagnostico.brechas_criticas : null} />
          <Contador id="hallazgos-abiertos" etiqueta="Hallazgos abiertos" valor={fila.hallazgos_abiertos} />
          <Contador id="tareas-vencidas" etiqueta="Tareas vencidas" valor={fila.tareas_vencidas} />
        </dl>
      )}
      {fila.cadena_integra === false && (
        <p role="note" className="badge-render-danger p-2 rounded-lg text-xs">
          <span aria-hidden="true">⚠ </span>
          Los diagnósticos sellados de esta organización no coinciden con su registro de integridad. No los uses como evidencia hasta que el equipo de EVYDENTIA lo revise.
        </p>
      )}
    </li>
  );
}

export default function CarteraTablero() {
  const [estado, setEstado] = React.useState<Estado>({ fase: "cargando" });
  const [pendiente, setPendiente] = React.useState<FilaCartera | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const activa = leerOrganizacionActiva();
  const email = leerSesion()?.email;

  const [intento, setIntento] = React.useState(0);

  React.useEffect(() => {
    let vivo = true;
    setEstado({ fase: "cargando" });
    consultarCartera()
      .then((filas) => vivo && setEstado({ fase: "listo", filas }))
      .catch(() => vivo && setEstado({ fase: "error" }));
    return () => {
      vivo = false;
    };
  }, [intento]);

  const cambiar = (fila: FilaCartera) => {
    if (!email) return;
    cambiarDeOrganizacion(email, aOrganizacion(fila));
    window.location.assign("/dashboard");
  };

  const entrar = (fila: FilaCartera) => {
    if (useAuditStore.getState().cambiosSinGuardar) {
      setPendiente(fila);
      return;
    }
    cambiar(fila);
  };

  const resolver = (decision: "guardar" | "descartar") => {
    if (!pendiente) return;
    if (!resolverCambiosSinGuardar(decision)) {
      setError("No se pudo guardar: el almacenamiento del navegador no está disponible.");
      setPendiente(null);
      return;
    }
    cambiar(pendiente);
  };

  return (
    <section aria-label="Tablero de cartera" className="space-y-4">
      {estado.fase === "cargando" && <p role="status" className="text-xs text-[var(--ui-texto-suave)]">Cargando la cartera…</p>}
      {estado.fase === "error" && (
        <div role="alert" className="badge-render-danger p-3 rounded-xl text-xs flex items-center justify-between gap-3">
          <span>No pudimos cargar tu cartera. Inténtalo de nuevo.</span>
          <button type="button" onClick={() => setIntento((n) => n + 1)} className="px-3 py-1 rounded-lg border border-[var(--ui-borde)] font-semibold cursor-pointer">Reintentar</button>
        </div>
      )}
      {error && <p role="alert" className="badge-render-danger p-3 rounded-xl text-xs">{error}</p>}
      {estado.fase === "listo" && estado.filas.length === 0 && (
        <p role="status" className="badge-render-warning p-3 rounded-xl text-xs">
          Tu cuenta todavía no pertenece a ninguna organización. Pide una invitación a quien administra tu cuenta.
        </p>
      )}
      {estado.fase === "listo" && estado.filas.length > 0 && (
        <ul aria-label="Organizaciones de la cartera" className="space-y-3">
          {estado.filas.map((f) => (
            <FilaOrganizacion
              key={f.tenant_id}
              fila={f}
              activa={activa?.tenant_id === f.tenant_id || !email}
              onEntrar={entrar}
            />
          ))}
        </ul>
      )}
      {pendiente && (
        <div role="alertdialog" aria-modal="true" aria-labelledby="titulo-cambios-cartera" className="fixed inset-0 flex items-center justify-center bg-zinc-900/40 px-4">
          <div className="w-full max-w-sm rounded-xl bg-[var(--ui-superficie)] p-6 shadow-lg space-y-3">
            <h2 id="titulo-cambios-cartera" className="text-base font-semibold">Tienes cambios sin guardar</h2>
            <p className="text-sm text-[var(--ui-texto-suave)]">
              Son de {activa?.nombre_comercial ?? "la organización actual"} y no pasarán a {pendiente.nombre}. ¿Qué hacemos con ellos antes de cambiar?
            </p>
            <div className="flex flex-col gap-2">
              <button type="button" onClick={() => resolver("guardar")} className="rounded-md border border-[var(--ui-borde)] px-3 py-2 text-sm font-semibold cursor-pointer">Guardar y cambiar</button>
              <button type="button" onClick={() => resolver("descartar")} className="rounded-md border border-[var(--ui-borde)] px-3 py-2 text-sm cursor-pointer">Descartar y cambiar</button>
              <button type="button" onClick={() => setPendiente(null)} className="px-3 py-2 text-sm text-[var(--ui-texto-suave)] cursor-pointer">Cancelar</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
