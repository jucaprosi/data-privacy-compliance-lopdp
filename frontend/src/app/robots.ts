import type { MetadataRoute } from "next";
import { esProduccion } from "@/lib/entorno";

/** EP-02: fuera de producción nadie indexa. En producción no se restringe nada, como hasta hoy. ¤entorno-pruebas */
export default function robots(): MetadataRoute.Robots {
  return esProduccion()
    ? { rules: { userAgent: "*", allow: "/" } }
    : { rules: { userAgent: "*", disallow: "/" } };
}
