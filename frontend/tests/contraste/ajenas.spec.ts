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
 * La lógica vive en `ajenas.ts` (no es prueba), que también importa `rutas.spec.ts`.
 * Las pruebas usan fichas y listas de fixture en un directorio temporal: no dependen del estado real de las fichas.
 *
 * Mutaciones (cada una hace fallar la prueba que se indica):
 *  - m1: medir siempre una ajena, aunque su dueña no esté hecha -> «m1 · una ajena de una ficha sin hacer queda pendiente».
 *  - m2: aceptar en `pendientes/` una línea de archivo ajeno -> «m2 · una línea de pendientes con archivo ajeno falla y nombra a la dueña».
 *  - m3: tratar una ajena sin dueño como medida -> «m3 · una ajena sin dueño queda pendiente y avisa al Arquitecto».
 */
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { expect, test } from "@playwright/test";
import { ajenasDe, leerFichas, pendientesPropias, SIN_DUENO } from "./ajenas";

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
