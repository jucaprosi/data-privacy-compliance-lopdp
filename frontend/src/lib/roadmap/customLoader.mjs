import { cwd } from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";
import fs from "node:fs";
import path from "node:path";

export async function resolve(specifier, context, defaultResolve) {
  const { parentURL = pathToFileURL(`${cwd()}/`).href } = context;

  // Si es un import relativo o absoluto local sin extensión
  if (specifier.startsWith("./") || specifier.startsWith("../") || specifier.startsWith("/")) {
    try {
      return await defaultResolve(specifier, context);
    } catch (err) {
      if (err.code === "ERR_MODULE_NOT_FOUND") {
        const parentPath = fileURLToPath(parentURL);
        const basePath = path.resolve(path.dirname(parentPath), specifier);
        
        // Probar si existe con .ts
        if (fs.existsSync(`${basePath}.ts`)) {
          return defaultResolve(`${specifier}.ts`, context);
        }
        // Probar si existe como directorio con /index.ts
        if (fs.existsSync(path.join(basePath, "index.ts"))) {
          return defaultResolve(`${specifier}/index.ts`, context);
        }
      }
      throw err;
    }
  }

  return defaultResolve(specifier, context);
}
