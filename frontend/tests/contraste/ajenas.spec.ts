// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa ¤arbitro
// ¤¤frontend-ide
/**
 * FE-44 · La ola de contraste sin encadenar (governance/especificaciones/FE-44.md).
 * Cada ficha mide lo suyo y anota los rojos ajenos, sin esperar a otra ni pedir un PR de gobernanza.
 *
 *  - R1: el dueño de una ruta o vista roja es la ficha cuya `propiedad` contiene el archivo que la causa.
 *  - R2: `pendientes/<FICHA>.txt` solo admite líneas cuyo `# <archivo>` esté en la `propiedad` de esa ficha.
 *  - R3: `ajenas/<FICHA>.txt` lleva los rojos de archivos ajenos: con la dueña sin terminar quedan en `test.fixme`
 *    («ajena de <dueña>»); con la dueña hecha se miden; sin dueña, `test.fixme` («sin dueño: avisar al Arquitecto»).
 *  - R4: la cabecera TOML de `governance/tareas/*.md` se lee como texto (`estado` y `propiedad`); `archivo#SECCIÓN` es el archivo.
 *
 * La lógica vive aquí, sin navegador, y `rutas.spec.ts` la importa (sus pruebas rápidas se registran también allí).
 * Las pruebas usan fichas y listas de fixture en un directorio temporal: no dependen del estado real de las fichas.
 *
 * Mutaciones (cada una hace fallar la prueba que se indica):
 *  - m1: medir siempre una ajena, aunque su dueña no esté hecha -> «m1 · una ajena de una ficha sin hacer queda pendiente».
 *  - m2: aceptar en `pendientes/` una línea de archivo ajeno -> «m2 · una línea de pendientes con archivo ajeno falla y nombra a la dueña».
 *  - m3: tratar una ajena sin dueño como medida -> «m3 · una ajena sin dueño queda pendiente y avisa al Arquitecto».
 */
import { mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { expect, test } from "@playwright/test";

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

// ---------------------------------------------------------------- pruebas con fixtures
function fixture(fichas: Record<string, { estado: string; propiedad: string[] }>, pendientes: Record<string, string> = {}, ajenas: Record<string, string> = {}) {
  const raiz = mkdtempSync(join(tmpdir(), "fe44-"));
  for (const d of ["tareas", "pendientes", "ajenas"]) mkdirSync(join(raiz, d));
  for (const [id, f] of Object.entries(fichas)) {
    const lista = f.propiedad.map((p) => `"${p}"`).join(", ");
    writeFileSync(join(raiz, "tareas", `${id}.md`), `+++\nid = "${id}"\nestado = "${f.estado}"\npropiedad = [${lista}]\n+++\n\n# ${id}\n`);
  }
  for (const [id, texto] of Object.entries(pendientes)) writeFileSync(join(raiz, "pendientes", `${id}.txt`), texto);
  for (const [id, texto] of Object.entries(ajenas)) writeFileSync(join(raiz, "ajenas", `${id}.txt`), texto);
  return { raiz, fichas: () => leerFichas(join(raiz, "tareas")), pendientes: join(raiz, "pendientes"), ajenas: join(raiz, "ajenas") };
}

test.describe("FE-44 · cada ficha mide lo suyo", () => {
  test("m1 · una ajena de una ficha sin hacer queda pendiente y, al hacerla, se mide", () => {
    const fx = fixture(
      { "FE-33": { estado: "en_curso", propiedad: ["frontend/src/app/login/page.tsx"] }, "FE-90": { estado: "en_curso", propiedad: ["frontend/src/components/Ajeno.tsx"] } },
      {},
      { "FE-33": "/login  # frontend/src/components/Ajeno.tsx\n" },
    );
    try {
      const antes = ajenasDe(fx.ajenas, fx.fichas()).get("/login");
      expect(antes, "ajena con la dueña sin hacer").toEqual({ ficha: "FE-33", pendiente: true, etiqueta: "ajena de FE-90" });
      writeFileSync(join(fx.raiz, "tareas", "FE-90.md"), readFileSync(join(fx.raiz, "tareas", "FE-90.md"), "utf8").replace("en_curso", "hecha"));
      const despues = ajenasDe(fx.ajenas, fx.fichas()).get("/login");
      expect(despues?.pendiente, "con la dueña hecha se mide: un cierre incompleto se ve en rojo").toBe(false);
    } finally {
      rmSync(fx.raiz, { recursive: true, force: true });
    }
  });

  test("m2 · una línea de pendientes con archivo ajeno falla y nombra a la dueña", () => {
    const fx = fixture(
      { "FE-35": { estado: "en_curso", propiedad: ["frontend/src/a.tsx"] }, "FE-43": { estado: "pendiente", propiedad: ["frontend/src/components/conocimiento/AyudaView.tsx"] } },
      { "FE-35": "vista:ayuda_conocimiento  # frontend/src/components/conocimiento/AyudaView.tsx\n" },
    );
    try {
      expect(() => pendientesPropias(fx.pendientes, fx.fichas())).toThrow(/FE-43/);
    } finally {
      rmSync(fx.raiz, { recursive: true, force: true });
    }
  });

  test("m3 · una ajena sin dueño queda pendiente y avisa al Arquitecto", () => {
    const fx = fixture(
      { "FE-33": { estado: "en_curso", propiedad: ["frontend/src/app/login/page.tsx"] } },
      {},
      { "FE-33": "vista:huerfana  # frontend/src/components/SinDueno.tsx\n" },
    );
    try {
      expect(ajenasDe(fx.ajenas, fx.fichas()).get("vista:huerfana")).toEqual({ ficha: "FE-33", pendiente: true, etiqueta: SIN_DUENO });
    } finally {
      rmSync(fx.raiz, { recursive: true, force: true });
    }
  });

  test("R2 · las líneas con archivo propio, con comentario final y con sección pasan", () => {
    const fx = fixture(
      { "FE-42": { estado: "pendiente", propiedad: ["frontend/src/a.tsx#SEC", "frontend/src/app/x/[token]/page.tsx", "frontend/tests/contraste/estados/FE-38.ts"] } },
      { "FE-42": "# cabecera\nvista:a  # frontend/src/a.tsx\n/x/[token]  # frontend/src/app/x/[token]/page.tsx (comentario)\nvista:n  # frontend/tests/contraste/estados/FE-38.ts (apertura)\n" },
    );
    try {
      expect([...pendientesPropias(fx.pendientes, fx.fichas()).keys()]).toEqual(["vista:a", "/x/[token]", "vista:n"]);
    } finally {
      rmSync(fx.raiz, { recursive: true, force: true });
    }
  });

  test("R2 · una línea sin archivo falla y dice en qué lista y línea está", () => {
    const fx = fixture({ "FE-41": { estado: "en_curso", propiedad: ["frontend/src/a.tsx"] } }, { "FE-41": "# c\n/aceptar/[token]  # (preparación del token de FE-41)\n" });
    try {
      expect(() => pendientesPropias(fx.pendientes, fx.fichas())).toThrow(/pendientes\/FE-41\.txt:2/);
    } finally {
      rmSync(fx.raiz, { recursive: true, force: true });
    }
  });

  test("R2 · un archivo de nadie en pendientes falla y pide avisar al Arquitecto", () => {
    const fx = fixture({ "FE-41": { estado: "en_curso", propiedad: ["frontend/src/a.tsx"] } }, { "FE-41": "vista:z  # frontend/src/Nadie.tsx\n" });
    try {
      expect(() => pendientesPropias(fx.pendientes, fx.fichas())).toThrow(/sin dueño \(avisar al Arquitecto\)/);
    } finally {
      rmSync(fx.raiz, { recursive: true, force: true });
    }
  });

  test("R4 · la propiedad con rutas entre corchetes, secciones y varias líneas se lee entera", () => {
    const fx = fixture({ "FE-33": { estado: "pendiente", propiedad: ["frontend/src/app/aceptar/[token]/page.tsx", "app/rat.py#ADPA-04"] } });
    try {
      writeFileSync(join(fx.raiz, "tareas", "FE-33.md"), '+++\nid = "FE-33"\nestado = "pendiente"\npropiedad = [\n  "frontend/src/app/aceptar/[token]/page.tsx",\n  "app/rat.py#ADPA-04",\n]\narbitro = "x"\n+++\n');
      expect(fx.fichas().get("FE-33")).toEqual({ id: "FE-33", estado: "pendiente", propiedad: ["frontend/src/app/aceptar/[token]/page.tsx", "app/rat.py#ADPA-04"] });
    } finally {
      rmSync(fx.raiz, { recursive: true, force: true });
    }
  });

  test("R3 · un archivo con sección cuenta como el archivo y una dueña hecha entre varias no basta", () => {
    const fx = fixture(
      { "FE-33": { estado: "en_curso", propiedad: ["a.tsx"] }, "FE-10": { estado: "hecha", propiedad: ["comun.ts"] }, "FE-43": { estado: "pendiente", propiedad: ["comun.ts#S"] } },
      {},
      { "FE-33": "vista:c  # comun.ts\n" },
    );
    try {
      expect(ajenasDe(fx.ajenas, fx.fichas()).get("vista:c")).toEqual({ ficha: "FE-33", pendiente: true, etiqueta: "ajena de FE-43" });
    } finally {
      rmSync(fx.raiz, { recursive: true, force: true });
    }
  });
});
