// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa ¤arbitro
// ¤¤frontend-ide
/**
 * FE-44 · Lector de fichas, de `pendientes/` y de `ajenas/` (R2 a R4). No es prueba: lo importan `rutas.spec.ts` y `ajenas.spec.ts`
 * (Playwright no deja que un spec importe a otro). Sin navegador.
 */
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

export type Ficha = { id: string; estado: string; propiedad: string[] };
export type Ajena = { ficha: string; pendiente: boolean; etiqueta: string };

/** Etiqueta de una ajena cuyo archivo no está en la propiedad de ninguna ficha. */
export const SIN_DUENO = "sin dueño: avisar al Arquitecto";

/** Quita la sección de un archivo con sección: `ruta/archivo.py#ADPA-04` es `ruta/archivo.py` (R4). */
const sinSeccion = (archivo: string) => archivo.split("#")[0];

/** R4: lee `estado` y `propiedad` de la cabecera TOML (entre los dos `+++`) de cada `<dir>/*.md`, como texto. */
export function leerFichas(dir: string): Map<string, Ficha> {
  const fichas = new Map<string, Ficha>();
  for (const nombre of readdirSync(dir).filter((n) => n.endsWith(".md")).sort()) {
    const texto = readFileSync(join(dir, nombre), "utf8").replace(/\r\n/g, "\n");
    if (!texto.startsWith("+++\n")) continue;
    const fin = texto.indexOf("\n+++", 4);
    if (fin < 0) continue;
    const cabecera = texto.slice(4, fin);
    const id = /^id\s*=\s*"([^"]+)"/m.exec(cabecera)?.[1];
    if (!id) continue;
    const estado = /^estado\s*=\s*"([^"]*)"/m.exec(cabecera)?.[1] ?? "";
    fichas.set(id, { id, estado, propiedad: leerLista(cabecera, "propiedad") });
  }
  return fichas;
}

/** Cadenas entre comillas de `clave = [ ... ]`, recorridas una a una (una ruta como `[token]` trae corchetes). */
function leerLista(cabecera: string, clave: string): string[] {
  const inicio = new RegExp(`^${clave}\\s*=\\s*\\[`, "m").exec(cabecera);
  if (!inicio) return [];
  const elementos: string[] = [];
  let i = inicio.index + inicio[0].length;
  while (i < cabecera.length && cabecera[i] !== "]") {
    if (cabecera[i] === '"') {
      const cierre = cabecera.indexOf('"', i + 1);
      if (cierre < 0) break;
      elementos.push(cabecera.slice(i + 1, cierre));
      i = cierre + 1;
    } else i++;
  }
  return elementos;
}

/** Líneas `<ruta o vista>  # <archivo> (comentario)` de una lista: la unidad y el archivo que la justifica. */
function lineasDe(archivo: string): { unidad: string; archivo: string | null; numero: number }[] {
  const lineas: { unidad: string; archivo: string | null; numero: number }[] = [];
  readFileSync(archivo, "utf8").split(/\r?\n/).forEach((linea, i) => {
    const [cuerpo, ...resto] = linea.split("#");
    const unidad = cuerpo.trim();
    if (!unidad) return; // vacía o solo comentario
    const primero = resto.join("#").trim().split(/\s+/)[0] ?? "";
    lineas.push({ unidad, archivo: /[./]/.test(primero) ? sinSeccion(primero) : null, numero: i + 1 });
  });
  return lineas;
}

const listasDe = (dir: string) => readdirSync(dir).filter((n) => /^FE-\d+\.txt$/.test(n)).sort();

/** Fichas, distintas de `propia`, cuya propiedad contiene el archivo. Las que no están hechas van primero (R1). */
function duenosDe(archivo: string, fichas: Map<string, Ficha>, propia?: string): Ficha[] {
  const duenos = [...fichas.values()].filter((f) => f.id !== propia && f.propiedad.some((p) => sinSeccion(p) === archivo));
  const sinHacer = duenos.filter((f) => f.estado !== "hecha");
  return sinHacer.length ? sinHacer : duenos;
}

/** R2: líneas de `pendientes/FE-NN.txt`. Una línea cuyo archivo no esté en la propiedad de esa ficha da error con la dueña. */
export function pendientesPropias(dir: string, fichas: Map<string, Ficha>): Map<string, string> {
  const mapa = new Map<string, string>();
  const errores: string[] = [];
  for (const f of listasDe(dir)) {
    const id = f.replace(".txt", "");
    const propia = fichas.get(id);
    for (const { unidad, archivo, numero } of lineasDe(join(dir, f))) {
      const donde = `pendientes/${f}:${numero} «${unidad}»`;
      if (!propia) errores.push(`${donde}: no existe governance/tareas/${id}.md`);
      else if (!archivo) errores.push(`${donde}: no cita el archivo que la justifica («# <archivo>» de la propiedad de ${id})`);
      else if (!propia.propiedad.some((p) => sinSeccion(p) === archivo)) {
        const duenos = duenosDe(archivo, fichas, id).map((d) => d.id);
        errores.push(`${donde}: «${archivo}» es ${duenos.length ? `de ${duenos.join(", ")}` : "sin dueño (avisar al Arquitecto)"}, no de ${id}; va en ajenas/${id}.txt`);
      }
      if (propia && !mapa.has(unidad)) mapa.set(unidad, id);
    }
  }
  if (errores.length) throw new Error(`R2 (FE-44): pendientes con archivos ajenos:\n${errores.join("\n")}`);
  return mapa;
}

/** R3: líneas de `ajenas/FE-NN.txt`: quedan pendientes mientras la dueña no esté hecha; sin dueña, pendientes y con aviso. */
export function ajenasDe(dir: string, fichas: Map<string, Ficha>): Map<string, Ajena> {
  const mapa = new Map<string, Ajena>();
  for (const f of listasDe(dir)) {
    const id = f.replace(".txt", "");
    for (const { unidad, archivo } of lineasDe(join(dir, f))) {
      const duenos = archivo ? duenosDe(archivo, fichas, id) : [];
      const sinHacer = duenos.filter((d) => d.estado !== "hecha");
      const ajena: Ajena = !duenos.length
        ? { ficha: id, pendiente: true, etiqueta: SIN_DUENO }
        : sinHacer.length
          ? { ficha: id, pendiente: true, etiqueta: `ajena de ${sinHacer.map((d) => d.id).join(", ")}` }
          : { ficha: id, pendiente: false, etiqueta: "" };
      const previa = mapa.get(unidad);
      if (!previa || (!previa.pendiente && ajena.pendiente)) mapa.set(unidad, ajena);
    }
  }
  return mapa;
}
