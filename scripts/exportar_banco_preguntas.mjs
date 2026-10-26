#!/usr/bin/env node
/**
 * scripts/exportar_banco_preguntas.mjs
 *
 * Exporta las 80 preguntas del banco canónico del frontend (TypeScript) al
 * archivo JSON que consume el servidor (features/diagnostico/domain/banco_preguntas.json).
 *
 * Opciones:
 *   --verificar   Compara el JSON del servidor contra el banco del frontend y
 *                 termina con código 0 si son idénticos o código 1 si difieren.
 *   (sin flags)   Genera y escribe el JSON del servidor.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');
const require = createRequire(import.meta.url);

// Resolver TypeScript desde frontend/node_modules
const tsPathCandidates = [
  path.join(rootDir, 'frontend'),
  path.join(rootDir, '..', 'frontend'),
  process.cwd(),
];

let ts;
for (const cand of tsPathCandidates) {
  try {
    const resolved = require.resolve('typescript', { paths: [cand] });
    ts = require(resolved);
    break;
  } catch {
    // continuar probando candidatos
  }
}

if (!ts) {
  console.error('Error: No se pudo resolver "typescript" desde frontend/node_modules ni paths candidatos.');
  process.exit(1);
}

function transpileTsFile(relPath) {
  const fullPath = path.join(rootDir, relPath);
  let code = fs.readFileSync(fullPath, 'utf8');
  // Eliminar import type para evitar referencias no resueltas
  code = code.replace(/import\s+type\s+[^;]+;/g, '');
  const result = ts.transpileModule(code, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
    },
  });
  return result.outputText;
}

function cargarBancoFrontend() {
  const mod1 = { exports: {} };
  new Function('exports', 'module', transpileTsFile('frontend/src/lib/bancoPreguntas/bloque1.ts'))(mod1.exports, mod1);

  const mod2 = { exports: {} };
  new Function('exports', 'module', transpileTsFile('frontend/src/lib/bancoPreguntas/bloque2.ts'))(mod2.exports, mod2);

  const mod3 = { exports: {} };
  new Function('exports', 'module', transpileTsFile('frontend/src/lib/bancoPreguntas/bloque3.ts'))(mod3.exports, mod3);

  const modEj = { exports: {} };
  new Function('exports', 'module', transpileTsFile('frontend/src/lib/bancoPreguntas/ejemplos.ts'))(modEj.exports, modEj);

  const all = [
    ...(mod1.exports.BLOQUE_1 || []),
    ...(mod2.exports.BLOQUE_2 || []),
    ...(mod3.exports.BLOQUE_3 || []),
  ].sort((a, b) => a.id - b.id);

  if (all.length !== 80) {
    throw new Error(`Se esperaban 80 preguntas en el frontend, se obtuvieron ${all.length}`);
  }

  return all.map((p) => ({
    id: p.id,
    dimensionId: p.dimensionId,
    control: p.control,
    enunciado: p.enunciado,
    enunciadoPorTamano: p.enunciadoPorTamano || {},
    ejemplo: modEj.exports.ejemploDePregunta(p.id, p.evidenciaEsperada),
    referenciaNormativa: p.referenciaNormativa,
    criticidad: p.criticidad,
    evidenciaEsperada: p.evidenciaEsperada,
    evidenciaPorTamano: p.evidenciaPorTamano || {},
    tamanoMinimo: p.tamanoMinimo,
    esEstructural: p.esEstructural ?? false,
  }));
}

const targetJsonPath = path.join(rootDir, 'features/diagnostico/domain/banco_preguntas.json');

const args = process.argv.slice(2);
const verificar = args.includes('--verificar');

try {
  const preguntasFrontend = cargarBancoFrontend();
  const jsonGenerado = JSON.stringify(preguntasFrontend, null, 2) + '\n';

  if (verificar) {
    if (!fs.existsSync(targetJsonPath)) {
      console.error(`ERROR: El archivo ${targetJsonPath} no existe.`);
      process.exit(1);
    }
    const jsonActual = fs.readFileSync(targetJsonPath, 'utf8').replace(/\r\n/g, '\n');
    if (jsonActual !== jsonGenerado) {
      console.error('ERROR: El banco de preguntas en el servidor difiere del banco del frontend.');
      process.exit(1);
    }
    console.log('OK: El banco de preguntas del servidor coincide exactamente con el frontend (80 controles).');
    process.exit(0);
  } else {
    // Escribir archivo
    fs.mkdirSync(path.dirname(targetJsonPath), { recursive: true });
    fs.writeFileSync(targetJsonPath, jsonGenerado, 'utf8');
    console.log(`OK: Exportadas ${preguntasFrontend.length} preguntas a ${targetJsonPath}`);
  }
} catch (err) {
  console.error('Error al procesar el banco de preguntas:', err);
  process.exit(1);
}
