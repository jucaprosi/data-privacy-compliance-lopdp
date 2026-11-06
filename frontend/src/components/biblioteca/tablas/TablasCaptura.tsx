"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Tablas de captura de un borrador (BIB-203), montadas en la ranura `documento:editor`.
 *
 * - INV, RAT y LEG: ver filas, editar una y pegar hasta 100 desde una hoja de cálculo. Lo pegado se
 *   valida primero por fila y solo se confirma si no hay errores; el servidor guarda todo o nada.
 * - PLA: solo lectura desde el plan canónico; el estado es calculado y no se edita.
 * - Si una carga falla se informa con `role="status"`, nunca con `role="alert"`.
 */
import React from "react";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";
import {
  MAX_FILAS, confirmarFilas, editarFila, leerPlan, listarFilas, obtenerEsquemas, partirPegado, validarFilas,
  type ColumnaCaptura, type FilaCaptura, type FilaEntrada, type FilaPlan, type Previa, type TablaCaptura,
} from "@/lib/biblioteca/filas";

type Pestana = TablaCaptura | "PLA";
const PESTANAS: { id: Pestana; nombre: string }[] = [
  { id: "INV", nombre: "Inventario" }, { id: "RAT", nombre: "RAT" }, { id: "LEG", nombre: "Legitimación" },
  { id: "PLA", nombre: "Plan (solo lectura)" },
];

export interface ConfigTablasPruebas {
  borradorId?: string;
  roadmapId?: string;
}

declare global {
  interface Window {
    __LOPDP_TABLAS_PRUEBAS__?: ConfigTablasPruebas;
  }
}

function configPruebas(): ConfigTablasPruebas {
  return typeof window !== "undefined" ? window.__LOPDP_TABLAS_PRUEBAS__ ?? {} : {};
}

function TablaPlan({ roadmapId }: { roadmapId: string | undefined }) {
  const [filas, setFilas] = React.useState<FilaPlan[] | null>(null);
  const [aviso, setAviso] = React.useState<string | null>(null);
  React.useEffect(() => {
    if (!roadmapId) return;
    let vigente = true;
    leerPlan(roadmapId).then((f) => vigente && setFilas(f))
      .catch((e: Error) => vigente && setAviso(e.message));
    return () => { vigente = false; };
  }, [roadmapId]);
  if (!roadmapId) return <p role="status">No hay un plan canónico elegido.</p>;
  if (aviso) return <p role="status">{aviso}</p>;
  if (!filas) return <p role="status">Cargando el plan…</p>;
  return (
    <table aria-label="Plan (solo lectura)" className="w-full text-sm">
      <thead><tr><th>Tarea</th><th>Control</th><th>Inicio</th><th>Fin</th><th>Estado (calculado)</th></tr></thead>
      <tbody>
        {filas.map((f) => (
          <tr key={f.id}>
            <td>{f.titulo}</td><td>{f.control_ref}</td><td>{f.fecha_inicio ?? "—"}</td>
            <td>{f.fecha_fin ?? "—"}</td><td>{f.estado}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function FilaEditable({ fila, columnas, onGuardada }: {
  fila: FilaCaptura; columnas: ColumnaCaptura[]; onGuardada: (f: FilaCaptura) => void;
}) {
  const [datos, setDatos] = React.useState(fila.datos);
  const [mensaje, setMensaje] = React.useState<string | null>(null);
  const guardar = () => {
    setMensaje(null);
    editarFila(fila.id, datos, fila.revision)
      .then((f) => { onGuardada(f); setMensaje("Fila guardada."); })
      .catch((e: Error) => setMensaje(e.message));
  };
  return (
    <tr>
      <th scope="row">{fila.codigo}</th>
      {columnas.map((c) => (
        <td key={c.clave}>
          <input aria-label={`${c.etiqueta} de ${fila.codigo}`} value={datos[c.clave] ?? ""}
            onChange={(e) => setDatos({ ...datos, [c.clave]: e.target.value })} className="w-full border px-1" />
        </td>
      ))}
      <td>
        <button type="button" onClick={guardar} className="underline">Guardar {fila.codigo}</button>
        {mensaje && <span role="status" className="ml-2">{mensaje}</span>}
      </td>
    </tr>
  );
}

function TablaEditable({ borradorId, tabla, columnas }: {
  borradorId: string; tabla: TablaCaptura; columnas: ColumnaCaptura[];
}) {
  const [filas, setFilas] = React.useState<FilaCaptura[]>([]);
  const [aviso, setAviso] = React.useState<string | null>(null);
  const [pegado, setPegado] = React.useState("");
  const [pendientes, setPendientes] = React.useState<FilaEntrada[]>([]);
  const [previa, setPrevia] = React.useState<Previa | null>(null);
  const [resultado, setResultado] = React.useState<string | null>(null);

  React.useEffect(() => {
    let vigente = true;
    setAviso(null);
    listarFilas(borradorId, tabla).then((f) => vigente && setFilas(f))
      .catch((e: Error) => vigente && setAviso(e.message));
    return () => { vigente = false; };
  }, [borradorId, tabla]);

  const validar = () => {
    setResultado(null); setPrevia(null);
    const partidas = partirPegado(pegado, columnas);
    if (partidas.length > MAX_FILAS) { setResultado(`Se pegan hasta ${MAX_FILAS} filas por vez.`); return; }
    setPendientes(partidas);
    validarFilas(borradorId, tabla, partidas).then(setPrevia).catch((e: Error) => setResultado(e.message));
  };
  const confirmar = () => {
    confirmarFilas(borradorId, tabla, pendientes)
      .then((nuevas) => {
        setFilas((f) => [...f, ...nuevas].sort((a, b) => a.codigo.localeCompare(b.codigo)));
        setResultado(`${nuevas.length} filas guardadas.`); setPrevia(null); setPegado("");
      })
      .catch((e: Error) => { setResultado(`${e.message} No se guardó ninguna fila.`); });
  };

  return (
    <div className="flex flex-col gap-3">
      {aviso && <p role="status">{aviso}</p>}
      <table aria-label={`Filas ${tabla}`} className="w-full text-sm">
        <thead><tr><th>Código</th>{columnas.map((c) => <th key={c.clave}>{c.etiqueta}</th>)}<th /></tr></thead>
        <tbody>
          {filas.map((f) => (
            <FilaEditable key={`${f.id}-${f.revision}`} fila={f} columnas={columnas}
              onGuardada={(n) => setFilas((xs) => xs.map((x) => (x.id === n.id ? n : x)))} />
          ))}
        </tbody>
      </table>
      <label className="flex flex-col gap-1">
        <span>Pegar filas (código y luego: {columnas.map((c) => c.etiqueta).join(", ")}; hasta {MAX_FILAS})</span>
        <textarea aria-label="Filas pegadas" value={pegado} onChange={(e) => setPegado(e.target.value)}
          rows={4} className="border p-1 font-mono" />
      </label>
      <div className="flex gap-2">
        <button type="button" onClick={validar} disabled={!pegado.trim()} className="border px-2">Validar filas</button>
        <button type="button" onClick={confirmar} disabled={!previa?.valida} className="border px-2">
          Confirmar {pendientes.length} filas
        </button>
      </div>
      {previa && (
        <ul aria-label="Validación previa">
          {previa.filas.map((r) => (
            <li key={r.indice}>
              Fila {r.indice + 1} ({r.codigo || "sin código"}): {r.errores.length ? r.errores.join(" ") : "correcta"}
            </li>
          ))}
        </ul>
      )}
      {resultado && <p role="status">{resultado}</p>}
    </div>
  );
}

export default function TablasCaptura() {
  const documentoId = useSeleccionBiblioteca((s) => s.documentoId);
  const cfg = configPruebas();
  const borradorId = cfg.borradorId ?? documentoId;
  const [pestana, setPestana] = React.useState<Pestana>("INV");
  const [esquemas, setEsquemas] = React.useState<Record<TablaCaptura, ColumnaCaptura[]> | null>(null);
  const [aviso, setAviso] = React.useState<string | null>(null);

  const [disponible, setDisponible] = React.useState(false);

  React.useEffect(() => {
    setDisponible(false); setEsquemas(null); setAviso(null);
    if (!borradorId) return;
    let vigente = true;
    let hay = false;
    // Solo se muestra si el documento elegido es un borrador estructurado con tablas; si no, no ocupa sitio.
    listarFilas(borradorId, "INV")
      .then(() => {
        if (!vigente) return;
        hay = true;
        setDisponible(true);
        return obtenerEsquemas().then((e) => vigente && setEsquemas(e));
      })
      .catch((e: Error) => vigente && hay && setAviso(e.message));
    return () => { vigente = false; };
  }, [borradorId]);

  if (!borradorId || !disponible) return null;
  return (
    <section aria-label="Tablas de captura" className="flex flex-col gap-3">
      <h3 className="font-semibold">Tablas de captura</h3>
      <p className="text-xs">Datos del borrador: no sustituyen al RAT ni al plan, ni son fuente validada.</p>
      <div role="tablist" aria-label="Tablas" className="flex gap-2">
        {PESTANAS.map((p) => (
          <button key={p.id} type="button" role="tab" aria-selected={pestana === p.id}
            onClick={() => setPestana(p.id)} className="border px-2">{p.nombre}</button>
        ))}
      </div>
      {pestana === "PLA" ? <TablaPlan roadmapId={cfg.roadmapId} />
        : aviso ? <p role="status">{aviso}</p>
          : !esquemas ? <p role="status">Cargando columnas…</p>
            : <TablaEditable borradorId={borradorId} tabla={pestana} columnas={esquemas[pestana]} />}
    </section>
  );
}
