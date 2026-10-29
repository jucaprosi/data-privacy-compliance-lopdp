// ¤asistente
// Monta la página de prueba del asistente sin pasar por la aplicación (FE-23).
//
// El repositorio no tiene pruebas de componentes de Playwright ni un empaquetador aparte, y la
// página de prueba no puede vivir en src/app. Este montador transpila con el `typescript` del
// proyecto (ya es dependencia) los .ts/.tsx alcanzables desde PaginaPrueba.tsx, los enlaza en un
// único script CommonJS con las compilaciones de desarrollo de React que hay en node_modules y lo
// inyecta en una página en blanco. No sirve nada por red ni depende del servidor de desarrollo.
import * as fs from "fs";
import * as path from "path";
import * as ts from "typescript";
import type { Page } from "@playwright/test";

const FRONTEND = path.resolve(__dirname, "..", "..");
const NODE_MODULES = path.join(FRONTEND, "node_modules");
const ENTRADA = path.join(__dirname, "PaginaPrueba.tsx");

/** Paquetes externos admitidos y su compilación CommonJS de desarrollo. */
const PAQUETES: Record<string, string> = {
  react: "react/cjs/react.development.js",
  "react/jsx-runtime": "react/cjs/react-jsx-runtime.development.js",
  "react-dom": "react-dom/cjs/react-dom.development.js",
  "react-dom/client": "react-dom/cjs/react-dom-client.development.js",
  scheduler: "scheduler/cjs/scheduler.development.js",
};

interface Modulo {
  codigo: string;
  dependencias: Record<string, string>;
}

function resolverLocal(desde: string, especificador: string): string {
  const base = path.resolve(path.dirname(desde), especificador);
  const candidatos = [base, `${base}.tsx`, `${base}.ts`, path.join(base, "index.tsx"), path.join(base, "index.ts")];
  const hallado = candidatos.find((c) => fs.existsSync(c) && fs.statSync(c).isFile());
  if (!hallado) throw new Error(`montaje: no se resuelve «${especificador}» desde ${desde}`);
  return hallado;
}

function resolver(desde: string, especificador: string): string {
  if (especificador.startsWith(".")) return resolverLocal(desde, especificador);
  const relativo = PAQUETES[especificador];
  if (!relativo) throw new Error(`montaje: paquete no admitido en la página de prueba: «${especificador}»`);
  return path.join(NODE_MODULES, relativo);
}

function leer(archivo: string): string {
  const fuente = fs.readFileSync(archivo, "utf-8");
  if (!/\.tsx?$/.test(archivo)) return fuente;
  return ts.transpileModule(fuente, {
    fileName: archivo,
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2019,
      jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true,
    },
  }).outputText;
}

/** Script autocontenido que monta la página de prueba en #raiz. */
export function empaquetarPaginaPrueba(): string {
  const modulos = new Map<string, Modulo>();
  const pendientes = [ENTRADA];
  while (pendientes.length) {
    const archivo = pendientes.pop() as string;
    if (modulos.has(archivo)) continue;
    const codigo = leer(archivo);
    const dependencias: Record<string, string> = {};
    for (const [, especificador] of codigo.matchAll(/require\("([^"]+)"\)/g)) {
      const destino = resolver(archivo, especificador);
      dependencias[especificador] = destino;
      pendientes.push(destino);
    }
    modulos.set(archivo, { codigo, dependencias });
  }
  const definiciones = [...modulos.entries()]
    .map(
      ([id, m]) =>
        `${JSON.stringify(id)}: [function (module, exports, require) {\n${m.codigo}\n}, ${JSON.stringify(m.dependencias)}]`,
    )
    .join(",\n");
  return `var process = { env: { NODE_ENV: "development" } };
(function () {
  var definiciones = {${definiciones}};
  var cache = {};
  function cargar(id) {
    if (cache[id]) return cache[id].exports;
    var def = definiciones[id];
    var module = { exports: {} };
    cache[id] = module;
    def[0].call(module.exports, module, module.exports, function (esp) { return cargar(def[1][esp]); });
    return module.exports;
  }
  cargar(${JSON.stringify(ENTRADA)});
})();`;
}

let cacheScript: string | null = null;

/** Abre la página de prueba del asistente en `page`. */
export async function abrirPaginaPrueba(page: Page): Promise<void> {
  cacheScript ??= empaquetarPaginaPrueba();
  await page.setContent('<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Asistente</title></head><body><div id="raiz"></div></body></html>');
  await page.addScriptTag({ content: cacheScript });
  await page.getByRole("heading", { name: "Datos generales" }).waitFor();
}
