"use client";

// ¤¤frontend-architect
// ¤frontend-ide ¤tablero-dimensiones
/**
 * Ficha resumen de la organización (FE-25): barra fija bajo el encabezado con el nombre, el sector, el
 * tamaño, las alertas abiertas y las cuatro dimensiones como semáforo. Sin cifra única. Se pliega y la
 * elección se recuerda; sin elección va abierta en escritorio y cerrada en móvil, donde queda una línea
 * con el nombre y las alertas. Sin dato del servidor se escribe «—»: nunca se afirma que no haya nadie.
 */
import React from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronUp, XCircle } from "lucide-react";
import { tenantConfigurado } from "@/lib/auth";
import { cargarFicha, type FichaResumenDatos } from "@/lib/fichaResumen";
import type { IdDimension, Semaforo } from "@/lib/tableros/resumen";

const VALOR: Record<Semaforo, string> = { success: "Favorable", warning: "Atención", danger: "Crítico" };
const ICONO = { success: CheckCircle2, warning: AlertTriangle, danger: XCircle } as const;

const DIMENSIONES: ReadonlyArray<{ id: IdDimension; etiqueta: string; base: string }> = [
  { id: "madurez", etiqueta: "Madurez", base: "Nivel de la dimensión más baja." },
  { id: "conformidad", etiqueta: "Cumplimiento", base: "Según los incumplimientos críticos abiertos." },
  { id: "evidencia", etiqueta: "Respaldo con documentos", base: "Según los documentos registrados." },
  { id: "riesgo", etiqueta: "Riesgo", base: "Según los riesgos críticos y altos abiertos." },
];

const CLAVE_PLEGADA = "ficha-resumen-plegada";
const ID_CUERPO = "ficha-resumen-cuerpo";

type Estado = { fase: "cargando" } | { fase: "error" } | { fase: "listo"; ficha: FichaResumenDatos | null };

const cifra = (n: number | null) => (n === null ? "Sin datos" : String(n));

function lineaCompacta(f: FichaResumenDatos): string {
  const t = f.tareasVencidas;
  const h = f.hallazgosAbiertos;
  const tareas =
    t === null ? "tareas vencidas: sin datos" : t === 0 ? "Sin tareas vencidas" : `${t} ${t === 1 ? "tarea vencida" : "tareas vencidas"}`;
  const hallazgos = h === null ? "hallazgos: sin datos" : `${h} ${h === 1 ? "hallazgo abierto" : "hallazgos abiertos"}`;
  return `${f.nombre} · ${tareas} · ${hallazgos}`;
}

function leerPlegada(): boolean | null {
  try {
    const v = window.sessionStorage.getItem(CLAVE_PLEGADA);
    return v === "1" ? true : v === "0" ? false : null;
  } catch {
    return null;
  }
}

function guardarPlegada(plegada: boolean): void {
  try {
    window.sessionStorage.setItem(CLAVE_PLEGADA, plegada ? "1" : "0");
  } catch {
    // Almacenamiento bloqueado: la elección simplemente no se recuerda.
  }
}

export default function FichaResumen() {
  const [estado, setEstado] = React.useState<Estado>({ fase: "cargando" });
  const [eleccion, setEleccion] = React.useState<boolean | null>(null);
  const [esEscritorio, setEsEscritorio] = React.useState(true);
  const [intento, setIntento] = React.useState(0);
  const tenant = tenantConfigurado();

  React.useEffect(() => {
    setEleccion(leerPlegada());
    const consulta = window.matchMedia("(min-width: 768px)");
    const alCambiar = () => setEsEscritorio(consulta.matches);
    alCambiar();
    consulta.addEventListener("change", alCambiar);
    return () => consulta.removeEventListener("change", alCambiar);
  }, []);

  React.useEffect(() => {
    let vivo = true;
    setEstado({ fase: "cargando" });
    cargarFicha(tenant)
      .then((ficha) => vivo && setEstado({ fase: "listo", ficha }))
      .catch(() => vivo && setEstado({ fase: "error" }));
    return () => {
      vivo = false;
    };
  }, [tenant, intento]);

  const plegada = eleccion ?? !esEscritorio;
  const alternar = () => {
    setEleccion(!plegada);
    guardarPlegada(!plegada);
  };

  const contenedor =
    "shrink-0 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 text-xs flex items-center gap-3";
  const alturaPlegada = "h-10 py-0";
  const alturaAbierta = "min-h-14 py-1.5";

  if (estado.fase === "cargando") {
    return (
      <section aria-label="Ficha de la organización" aria-busy="true" data-testid="ficha-resumen" className={`${contenedor} ${alturaAbierta}`}>
        <div role="status" className="flex w-full animate-pulse items-center gap-3">
          <span className="sr-only">Cargando la ficha de la organización</span>
          <span aria-hidden="true" className="h-3 w-40 rounded bg-[var(--ui-borde)]" />
          <span aria-hidden="true" className="h-3 w-24 rounded bg-[var(--ui-borde)]" />
          <span aria-hidden="true" className="h-3 w-24 rounded bg-[var(--ui-borde)]" />
        </div>
      </section>
    );
  }

  if (estado.fase === "error" || estado.ficha === null) {
    return (
      <section aria-label="Ficha de la organización" data-testid="ficha-resumen" className={`${contenedor} ${alturaAbierta}`}>
        <span role="status">No pudimos cargar la ficha de la organización. Inténtalo de nuevo.</span>
        <button
          type="button"
          aria-label="Volver a cargar la ficha de la organización"
          onClick={() => setIntento((n) => n + 1)}
          className="rounded border border-[var(--ui-borde)] px-2 py-1 font-medium cursor-pointer"
        >
          Volver a cargar
        </button>
      </section>
    );
  }

  const f = estado.ficha;

  if (plegada) {
    return (
      <section aria-label="Ficha de la organización" data-testid="ficha-resumen" className={`${contenedor} ${alturaPlegada}`}>
        <button
          type="button"
          aria-expanded={false}
          aria-controls={ID_CUERPO}
          title={f.nombre}
          onClick={alternar}
          className="flex min-w-0 flex-1 items-center gap-2 text-left cursor-pointer"
          data-testid="ficha-linea-compacta"
        >
          <ChevronDown className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          <span className="sr-only">Mostrar la ficha de la organización. {lineaCompacta(f)}</span>
          <span aria-hidden="true" className="min-w-0 truncate font-semibold">{lineaCompacta(f)}</span>
          <span aria-hidden="true" className="hidden shrink-0 font-medium md:inline">Mostrar la ficha</span>
        </button>
      </section>
    );
  }

  return (
    <section aria-label="Ficha de la organización" data-testid="ficha-resumen" className={`${contenedor} ${alturaAbierta}`}>
      <div id={ID_CUERPO} className="flex min-w-0 flex-1 flex-wrap items-center gap-x-4 gap-y-1">
        <span className="font-bold" data-testid="ficha-nombre" title={f.nombre}>{f.nombre}</span>
        {/* Lo que la cartera aún no envía se escribe «—»; no se inventa ni se lee de otra parte. */}
        <span className="text-[var(--ui-texto-suave)]">RUC: —</span>
        <span className="text-[var(--ui-texto-suave)]">Sector: —</span>
        <span className="text-[var(--ui-texto-suave)]">Tamaño: —</span>
        <span className="text-[var(--ui-texto-suave)]">Naturaleza: —</span>
        <span className="text-[var(--ui-texto-suave)]">DPO: {f.dpo ?? "—"}</span>
        <span className="text-[var(--ui-texto-suave)]">Consultor: {f.consultor ?? "—"}</span>
        <span data-testid="ficha-tareas-vencidas">Tareas vencidas: {cifra(f.tareasVencidas)}</span>
        <span data-testid="ficha-hallazgos">Hallazgos abiertos: {cifra(f.hallazgosAbiertos)}</span>
        <ul aria-label="Dimensiones" className="flex flex-wrap items-center gap-2">
          {DIMENSIONES.map((d) => {
            const tarjeta = f.dimensiones?.find((t) => t.id === d.id);
            if (!tarjeta) {
              return (
                <li
                  key={d.id}
                  data-testid={`ficha-dimension-${d.id}`}
                  title="Aparece cuando el DPO sella el diagnóstico."
                  className="flex items-center gap-1 text-[var(--ui-texto-suave)]"
                >
                  <span>{d.etiqueta}:</span>
                  <span>Sin diagnóstico sellado</span>
                </li>
              );
            }
            const Icono = ICONO[tarjeta.semaforo];
            return (
              <li key={d.id} data-testid={`ficha-dimension-${d.id}`} title={d.base} className="flex items-center gap-1">
                <span>{d.etiqueta}</span>
                <span className={`badge-render-${tarjeta.semaforo} inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-semibold`}>
                  <Icono className="h-3 w-3" aria-hidden="true" />
                  {VALOR[tarjeta.semaforo]}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
      <button
        type="button"
        aria-expanded={true}
        aria-controls={ID_CUERPO}
        onClick={alternar}
        className="inline-flex shrink-0 items-center gap-1 rounded border border-[var(--ui-borde)] px-2 py-1 font-medium cursor-pointer"
      >
        <ChevronUp className="h-3.5 w-3.5" aria-hidden="true" />
        <span>Ocultar la ficha<span className="sr-only"> de la organización</span></span>
      </button>
    </section>
  );
}
