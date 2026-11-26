// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa ¤cita-verificada
// ¤¤developer-architect
"use client";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import {
  CITAS_SIN_VERIFICAR, CONFLICTO_PROPUESTA, FORMATO_TEXTO, MOTIVOS, TEXTO_ESTADO,
  autoria, avisoPendiente, cambiarEstado, cargarArchivo, compararVersion, crearVersion, dictaminar, esDeLaIa,
  estadoVisible, fechaLarga, guardarFicha, leerHistorial, listarEditorial,
  type CatalogoEditorial, type Comparacion, type EventoEditorial, type Version,
} from "@/lib/biblioteca/editorial";
import { ComparacionVersion, LeyendaNota, hayCitasSinVerificar } from "./ComparacionVersion";
import {
  DialogoAprobar, DialogoDescartar, DialogoDevolver, DialogoProponer, MOTIVO_GENERAL,
} from "./DialogosVersionIa";
import { camposFicha, FichaEditorial } from "./FichaEditorial";
import { PermisosEditorialesPropios, SIN_PERMISOS_EDITORIALES } from "./PermisosEditorialesPropios";
import { ErrorBiblioteca } from "@/lib/biblioteca/http";

type Dialogo = "proponer" | "aprobar" | "devolver" | "descartar" | null;

/** Botón no disponible: `aria-disabled` con su motivo visible y enlazado por `aria-describedby`. */
function BotonCondicionado({ id, nombre, motivo, onClick, children }: {
  id: string; nombre: string; motivo: string | null; onClick: () => void; children?: ReactNode;
}) {
  const bloqueado = motivo !== null;
  return <div className="grid gap-1">
    <button type="button" aria-disabled={bloqueado || undefined} aria-describedby={bloqueado && motivo ? `motivo-${id}` : undefined}
      onClick={() => { if (!bloqueado) onClick(); }}
      className={`justify-self-start rounded border p-2 ${bloqueado ? "cursor-not-allowed opacity-70" : ""}`}>{nombre}</button>
    {bloqueado && motivo && <p id={`motivo-${id}`}>{motivo}</p>}
    {children}
  </div>;
}

export function AdministracionEditorial() {
  const [datos, setDatos] = useState<CatalogoEditorial | null>(null);
  const [error, setError] = useState("");
  const [sinPermisos, setSinPermisos] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [ocupada, setOcupada] = useState(false);
  const [seleccion, setSeleccion] = useState("");
  const [historial, setHistorial] = useState<EventoEditorial[] | null>(null);
  const [comparacion, setComparacion] = useState<Comparacion | null>(null);
  const [dialogo, setDialogo] = useState<Dialogo>(null);
  const [plantilla, setPlantilla] = useState("");
  const [codigo, setCodigo] = useState("");
  const [numero, setNumero] = useState("");
  const [formato, setFormato] = useState("DOCX");
  const [sustituye, setSustituye] = useState("");
  const [comentario, setComentario] = useState("");
  const [aprobado, setAprobado] = useState(true);
  const [motivo, setMotivo] = useState("");
  const [archivo, setArchivo] = useState<File | null>(null);
  const recargar = useCallback(async () => { setDatos(await listarEditorial()); }, []);
  useEffect(() => { recargar().catch(e => {
    setError(e.message); setSinPermisos(e instanceof ErrorBiblioteca && e.estado === 403);
  }); }, [recargar]);
  async function operar(accion: () => Promise<unknown>, texto: string) {
    setOcupada(true); setError(""); setMensaje("");
    try { await accion(); await recargar(); setMensaje(texto); setHistorial(null); }
    catch (e) { setError(e instanceof Error ? e.message : "No se pudo completar la operación."); }
    finally { setOcupada(false); }
  }
  const tiene = (capacidad: string) => datos?.capacidades.some(c => c === capacidad) ?? false;
  const version = datos?.versiones.find(v => v.id === seleccion);
  const delaIa = !!version && esDeLaIa(version);
  const independiente = !!version && !version.autores.includes(datos?.actor_id ?? "");
  const revisiones = datos?.revisiones.filter(r => r.version_id === version?.id) ?? [];
  const actuales = revisiones.filter(r => r.generacion === version?.generacion);
  const lista = version?.estado === "en_revision";
  const esMd = version?.formato === "MD";
  useEffect(() => {
    setComparacion(null);
    if (!version || !esMd) return;
    let vigente = true;
    compararVersion(version).then(c => { if (vigente) setComparacion(c); }).catch(() => undefined);
    return () => { vigente = false; };
    // La comparación se vuelve a pedir al cambiar de versión o de edición, no en cada recarga del listado.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version?.id, version?.generacion, esMd]);

  const citasSinVerificar = delaIa && hayCitasSinVerificar(comparacion);
  const faltan = !version ? [] : [
    !version.sha256 && !esMd && "el archivo",
    !version.ficha && "la ficha",
    !delaIa && !actuales.some(r => r.tipo === "tecnica" && r.aprobado) && "una revisión técnica aprobada",
    citasSinVerificar && "que las citas estén verificadas",
  ].filter((x): x is string => !!x);
  const completa = faltan.length === 0 && !!version?.ficha;
  const aviso = lista ? avisoPendiente(faltan) : null;
  function prepararSucesora(v: Version) { setSustituye(v.id); setCodigo(v.codigo); setFormato(v.formato === "MD" ? "DOCX" : v.formato); setNumero(""); }

  const porPlantilla = new Map<string, Version[]>();
  for (const v of datos?.versiones ?? []) porPlantilla.set(v.codigo, [...(porPlantilla.get(v.codigo) ?? []), v]);
  const publicadaDe = (cod: string) => porPlantilla.get(cod)?.find(v => v.estado === "publicada");
  const propuestaEnRevision = (cod: string) => porPlantilla.get(cod)?.find(v => esDeLaIa(v) && v.estado === "en_revision");
  const citaOrigen = comparacion?.secciones.flatMap(s => s.cambios).find(c => c.cita?.verificada)?.cita;

  return <main aria-label="Administración editorial" className="mx-auto max-w-6xl space-y-6 bg-[var(--ui-superficie)] p-6">
    <header><h1 className="text-2xl font-bold">Administración editorial</h1>
      <p>Versiones maestras de EVYDENTIA. Publicar requiere archivo, ficha y una revisión técnica aprobada.</p></header>
    {error && <p role="alert" className="rounded border border-[var(--ui-borde)] p-3">{error}</p>}
    {sinPermisos && <p role="status">{SIN_PERMISOS_EDITORIALES}</p>}
    {mensaje && <p role="status">{mensaje}</p>}
    {!datos && !error && <p role="status">Cargando administración editorial…</p>}
    <button onClick={() => void operar(recargar, "Listado actualizado")} disabled={ocupada}>Actualizar listado</button>
    {datos && <>
      <PermisosEditorialesPropios capacidades={datos.capacidades} />
      {tiene("editor") && <form className="flex flex-wrap items-end gap-3 rounded border p-4" onSubmit={e => {
        e.preventDefault(); void operar(async () => {
          const nueva = await crearVersion(codigo, numero, formato, sustituye || null); setSeleccion(nueva.id);
          setNumero(""); setSustituye("");
        }, "Versión creada en revisión; no está publicada.");
      }}>
        <label>Código<input aria-label="Código" className="block rounded border p-2" required pattern="[A-Z][A-Z0-9-]{1,39}"
          value={codigo} onChange={e => setCodigo(e.target.value)} readOnly={!!sustituye} /></label>
        <label>Versión<input aria-label="Versión nueva" className="block rounded border p-2" required pattern="[0-9]+\.[0-9]+(\.[0-9]+)?"
          value={numero} onChange={e => setNumero(e.target.value)} /></label>
        <label>Formato<select className="block rounded border p-2" value={formato} onChange={e => setFormato(e.target.value)}>
          <option>DOCX</option><option>XLSX</option></select></label>
        <button disabled={ocupada} className="rounded bg-[var(--ui-primario)] p-2 text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)]">Crear versión en revisión</button>
        {sustituye && <button type="button" onClick={() => setSustituye("")}>Cancelar sustitución</button>}
      </form>}
      <ul aria-label="Versiones maestras" className="grid gap-5">
        {[...porPlantilla.entries()].map(([cod, versiones]) => {
          const nombre = (publicadaDe(cod) ?? versiones[0]).ficha?.nombre ?? cod;
          const enRevision = propuestaEnRevision(cod);
          const puedeProponer = tiene("editor") || tiene("revisor_tecnico");
          return <li key={cod} className="grid gap-2">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left">
                <caption className="pb-2 text-left font-semibold">Versiones de {nombre}</caption>
                <thead><tr>{["Versión", "Formato", "Estado", "Autoría", "Origen", "Fecha"].map(c =>
                  <th key={c} scope="col" className="border-b p-2">{c}</th>)}</tr></thead>
                <tbody>{versiones.map(v => <tr key={v.id} className="border-b align-top">
                  <td className="p-2"><button aria-pressed={seleccion === v.id} onClick={() => { setSeleccion(v.id); setHistorial(null); setArchivo(null); }}>
                    {v.codigo} · {v.version}</button></td>
                  <td className="p-2">{FORMATO_TEXTO[v.formato]}</td>
                  <td className="p-2">{TEXTO_ESTADO[estadoVisible(v, datos.revisiones)]}</td>
                  <td className="p-2">{autoria(v)}</td>
                  <td className="p-2">{esDeLaIa(v) ? (v.origen_ia === "resolucion" ? "Resolución normativa" : "Petición") : "Cargada a mano"}</td>
                  <td className="p-2"><time dateTime={v.creada_en.slice(0, 10)}>{fechaLarga(v.creada_en)}</time></td>
                </tr>)}</tbody>
              </table>
            </div>
            {puedeProponer && <BotonCondicionado id={`proponer-${cod}`} nombre="Proponer cambio" motivo={enRevision ? CONFLICTO_PROPUESTA : null}
              onClick={() => { setPlantilla(cod); setDialogo("proponer"); }}>
              {enRevision && <a href={`#version-${enRevision.id}`} onClick={() => { setSeleccion(enRevision.id); setHistorial(null); }}>Ver la propuesta en revisión</a>}
            </BotonCondicionado>}
          </li>;
        })}
      </ul>
      {!datos.versiones.length && <p>No hay versiones maestras registradas.</p>}
      {version && <section id={`version-${version.id}`} className="grid gap-5 rounded border p-5" aria-label="Detalle editorial">
        <h2 className="text-xl font-semibold">Versión {version.version} · {TEXTO_ESTADO[estadoVisible(version, datos.revisiones)]}</h2>
        {version.estado === "publicada" && <LeyendaNota leyenda={version.leyenda} />}
        {delaIa && <p role="note">La redactó la IA. Revisa cada cambio y su cita antes de aprobarla.</p>}
        {delaIa && <section aria-label="Origen de esta versión" className="grid gap-1">
          <h3 className="font-semibold">Origen de esta versión</h3>
          {version.modelo_ia && <p>Modelo: {version.modelo_ia}</p>}
          {version.origen_ia === "peticion"
            ? <p>A partir de: petición de {version.solicitante_nombre ?? ""}{version.motivo_ia && version.motivo_ia !== MOTIVO_GENERAL ? `, «${version.motivo_ia}»` : ""}</p>
            : citaOrigen && <p>A partir de: {[citaOrigen.norma, citaOrigen.articulo].filter(Boolean).join(", ")}{citaOrigen.fecha_vigencia ? ` · entra en vigencia el ${fechaLarga(citaOrigen.fecha_vigencia)}` : ""}</p>}
        </section>}
        <p>Responsable editorial: {version.solicitante_nombre ?? version.responsable_id}.{!esMd && ` Archivo: ${version.nombre_archivo ?? "Pendiente"}.`}</p>
        {version.sha256 && <p className="break-all">Huella de integridad (SHA-256): {version.sha256}</p>}
        {esMd && comparacion && <ComparacionVersion comparacion={comparacion} />}
        {!delaIa && (lista && tiene("editor") ? <>
          <FichaEditorial key={`${version.id}:${version.generacion}`} version={version} ocupada={ocupada}
            guardar={f => operar(() => guardarFicha(version, f), "Ficha guardada; revisiones anteriores conservadas como historial.")} />
          {!esMd && <form className="grid gap-2" onSubmit={e => { e.preventDefault(); if (archivo) void operar(() => cargarArchivo(version, archivo), "Archivo guardado para revisión."); }}>
            <label>Archivo maestro (máximo 10 MB)<input type="file" required accept={version.formato === "DOCX" ? ".docx" : ".xlsx"}
              onChange={e => setArchivo(e.target.files?.[0] ?? null)} /></label>
            <button disabled={ocupada || !archivo}>Guardar archivo maestro</button>
          </form>}
        </> : <>
          {version.ficha && <dl>{camposFicha.map(([clave, etiqueta]) => <div key={clave}><dt className="font-semibold">{etiqueta}</dt><dd>{version.ficha?.[clave]}</dd></div>)}</dl>}
          {lista && !tiene("editor") && <BotonCondicionado id="guardar-ficha" nombre="Guardar ficha" motivo={MOTIVOS.editor} onClick={() => undefined} />}
        </>)}
        {delaIa && version.ficha && <dl>{camposFicha.map(([clave, etiqueta]) => <div key={clave}><dt className="font-semibold">{etiqueta}</dt><dd>{version.ficha?.[clave]}</dd></div>)}</dl>}
        <section aria-label="Dictámenes"><h3 className="font-semibold">Revisiones</h3>
          <p>Las revisiones anteriores se conservan; solo cuentan las de la edición actual.</p>
          {revisiones.filter(r => r.tipo === "tecnica").map((r, i) => <p key={i}>Técnica: {r.aprobado ? "Aprobada" : "Rechazada"} · {r.revisor_id} · edición {r.generacion} · {r.comentario}</p>)}
          {lista && !delaIa && <div className="grid gap-2">
            <label>Dictamen<textarea className="block w-full rounded border p-2" value={comentario} maxLength={4000} onChange={e => setComentario(e.target.value)} /></label>
            <label><input type="checkbox" checked={aprobado} onChange={e => setAprobado(e.target.checked)} /> Aprobar revisión</label>
            <BotonCondicionado id="revisar" nombre="Registrar revisión técnica"
              motivo={!tiene("revisor_tecnico") ? MOTIVOS.tecnico : !independiente ? MOTIVOS.revisar
                : ocupada || !comentario.trim() || actuales.some(r => r.tipo === "tecnica") ? "" : null}
              onClick={() => void operar(() => dictaminar(version, "tecnica", aprobado, comentario), "Dictamen registrado.")} />
          </div>}
        </section>
        {aviso && <p>{aviso}</p>}
        {lista && delaIa && <div className="grid gap-3">
          <BotonCondicionado id="aprobar" nombre="Aprobar y publicar"
            motivo={citasSinVerificar ? CITAS_SIN_VERIFICAR : !tiene("revisor_tecnico") ? MOTIVOS.tecnico : !tiene("publicador") ? MOTIVOS.publicador : null}
            onClick={() => setDialogo("aprobar")} />
          <BotonCondicionado id="devolver" nombre="Devolver con observaciones" motivo={tiene("revisor_tecnico") ? null : MOTIVOS.tecnico}
            onClick={() => setDialogo("devolver")} />
          <BotonCondicionado id="descartar" nombre="Descartar" motivo={null} onClick={() => setDialogo("descartar")} />
        </div>}
        {!delaIa && (lista || version.estado === "publicada") && <div className="grid gap-2">
          <label>Motivo de la decisión<textarea className="block w-full rounded border p-2" value={motivo} maxLength={2000} onChange={e => setMotivo(e.target.value)} /></label>
          {lista ? <BotonCondicionado id="publicar" nombre="Publicar versión"
            motivo={!tiene("publicador") ? MOTIVOS.publicador : !independiente ? MOTIVOS.publicar : ocupada || !completa || !motivo.trim() ? "" : null}
            onClick={() => void operar(() => cambiarEstado(version, "publicar", motivo), "Versión publicada.")} />
            : tiene("publicador") && independiente && <button disabled={ocupada || !motivo.trim()}
              onClick={() => void operar(() => cambiarEstado(version, "retirar", motivo), "Versión retirada; se conserva su historial.")}>Retirar versión</button>}
        </div>}
        {tiene("editor") && version.estado === "publicada" && <button onClick={() => prepararSucesora(version)}>Preparar versión sustituta</button>}
        {delaIa
          ? <section aria-label="Historial"><h3 className="font-semibold">Historial</h3><ul>
            <li><time dateTime={version.creada_en.slice(0, 10)}>{fechaLarga(version.creada_en)}</time> · Redactada por la IA</li>
            {revisiones.filter(r => r.tipo === "tecnica").map((r, i) => <li key={i}>
              <time dateTime={r.creada_en.slice(0, 10)}>{fechaLarga(r.creada_en)}</time> · {r.aprobado
                ? (version.estado === "publicada" ? `Aprobada y publicada por ${r.revisor_id}` : `Aprobada por ${r.revisor_id}`)
                : `Devuelta por ${r.revisor_id}`}</li>)}
          </ul></section>
          : <>
            <button disabled={ocupada} onClick={async () => {
              setOcupada(true); setError("");
              try { setHistorial(await leerHistorial(version)); }
              catch (e) { setError(e instanceof Error ? e.message : "No se pudo cargar el historial."); }
              finally { setOcupada(false); }
            }}>Ver historial editorial</button>
            {historial && <ul aria-label="Historial editorial">{historial.map((h, i) => <li key={i}>
              {h.accion} · {h.actor_id} · {new Date(h.creada_en).toLocaleString()} · {h.motivo}
            </li>)}</ul>}
          </>}
        {!independiente && !delaIa && <p>No puedes revisar ni publicar una versión en cuya elaboración participaste.</p>}
      </section>}
      {dialogo === "proponer" && <DialogoProponer codigo={plantilla} onCerrar={() => setDialogo(null)} onHecho={() => void recargar()} />}
      {dialogo === "aprobar" && version && <DialogoAprobar version={version} publicadaN={publicadaDe(version.codigo)?.version ?? null}
        onCerrar={() => setDialogo(null)} onHecho={() => void recargar()} />}
      {dialogo === "devolver" && version && <DialogoDevolver version={version} onCerrar={() => setDialogo(null)} onHecho={() => void recargar()} />}
      {dialogo === "descartar" && version && <DialogoDescartar version={version} onCerrar={() => setDialogo(null)} onHecho={() => void recargar()} />}
    </>}
  </main>;
}
