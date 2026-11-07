import type { MetadataRoute } from "next";
import { entornoDelServidor, esProduccion } from "@/lib/entorno";

/** EP-02: se decide al ejecutar con APP_ENV. Solo producción se indexa; sin APP_ENV válido, tampoco. ¤entorno-pruebas */
export const dynamic = "force-dynamic";

export default function robots(): MetadataRoute.Robots {
  return esProduccion(entornoDelServidor())
    ? { rules: { userAgent: "*", allow: "/" } }
    : { rules: { userAgent: "*", disallow: "/" } };
}
