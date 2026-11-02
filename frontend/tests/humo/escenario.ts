/**
 * Escenario de las pruebas de humo: dos organizaciones propias de la corrida y tokens firmados con la
 * clave temporal del arrancador (tests/humo/servidor_humo.py).
 *
 * Los datos se reparten por archivo porque preparación, limpieza y flujos corren en procesos distintos.
 */
import { createSign, randomBytes } from "crypto";
import * as fs from "fs";
import * as path from "path";

import type { Page } from "@playwright/test";

import { ejecutarSql } from "../integracion/dbHelper";

export const ROL_HUMO = "coordinador";

export interface OrganizacionHumo {
  tenantId: string;
  userId: string;
  email: string;
  nombre: string;
}

export interface Escenario {
  a: OrganizacionHumo;
  b: OrganizacionHumo;
}

const rutaEscenario = () => path.join(process.env.HUMO_DIR ?? "", "escenario.json");

export function leerEscenario(): Escenario {
  return JSON.parse(fs.readFileSync(rutaEscenario(), "utf-8")) as Escenario;
}

function crearOrganizacion(sufijo: string, letra: string): OrganizacionHumo {
  const tenantId = `org-humo-${letra}-${sufijo}`;
  const userId = `user-humo-${letra}-${sufijo}`;
  const email = `coordinador@${tenantId}.test`;
  const nombre = `Humo ${letra.toUpperCase()} ${sufijo}`;
  ejecutarSql([
    [
      "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano, activo) VALUES (%s, %s, %s, %s, %s, true)",
      [tenantId, nombre, `${nombre} S.A.`, `RUC${sufijo}${letra}`, null],
    ],
    ["INSERT INTO users (id, email, nombre) VALUES (%s, %s, %s)", [userId, email, "Coordinación de humo"]],
    [
      "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (%s, %s, %s, %s)",
      [`utr-humo-${letra}-${sufijo}`, userId, tenantId, ROL_HUMO],
    ],
  ]);
  return { tenantId, userId, email, nombre };
}

export function crearEscenario(): void {
  const sufijo = randomBytes(5).toString("hex");
  const escenario: Escenario = { a: crearOrganizacion(sufijo, "a"), b: crearOrganizacion(sufijo, "b") };
  fs.writeFileSync(rutaEscenario(), JSON.stringify(escenario));
}

/**
 * Borra todo lo de la organización sin una lista de tablas, que quedaría atrás en cuanto un módulo guarde
 * algo nuevo. Varias pasadas porque las claves foráneas fijan un orden que aquí no se conoce. Si queda una
 * fila, el DELETE final de `tenants` falla y la corrida lo dice.
 *
 * Las tablas con RLS forzado exigen el contexto de la organización, también para su dueño.
 */
function borrarOrganizacion(org: OrganizacionHumo): void {
  ejecutarSql([
    ["SELECT set_config('app.current_tenant_id', %s, true)", [org.tenantId]],
    [
      `DO $$
       DECLARE tabla text;
       BEGIN
         FOR pasada IN 1..5 LOOP
           FOR tabla IN
             SELECT c.table_name FROM information_schema.columns c
             JOIN information_schema.tables t USING (table_schema, table_name)
             WHERE c.table_schema = 'public' AND c.column_name = 'tenant_id' AND t.table_type = 'BASE TABLE'
           LOOP
             BEGIN
               EXECUTE format('DELETE FROM %%I WHERE tenant_id::text = %%L', tabla, '${org.tenantId}');
             EXCEPTION WHEN foreign_key_violation THEN NULL;
             END;
           END LOOP;
         END LOOP;
       END $$`,
      [],
    ],
    ["DELETE FROM users WHERE id = %s", [org.userId]],
    ["DELETE FROM tenants WHERE id = %s", [org.tenantId]],
  ]);
}

export function borrarEscenario(): void {
  if (!fs.existsSync(rutaEscenario())) return;
  const { a, b } = leerEscenario();
  borrarOrganizacion(a);
  borrarOrganizacion(b);
}

const base64Url = (datos: string | Buffer) => Buffer.from(datos).toString("base64url");

interface OpcionesToken {
  aud?: string;
  iss?: string;
  expEnSegundos?: number;
  clavePrivada?: string;
}

/** Token con la forma del de Google. Con `clavePrivada` se firma con otra clave, para los rechazos. */
export function firmarToken(org: OrganizacionHumo, opciones: OpcionesToken = {}): string {
  const ahora = Math.floor(Date.now() / 1000);
  const cabecera = base64Url(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const carga = base64Url(
    JSON.stringify({
      iss: opciones.iss ?? "https://accounts.google.com",
      aud: opciones.aud ?? process.env.HUMO_CLIENT_ID,
      sub: `sub-${org.userId}`,
      email: org.email,
      email_verified: true,
      name: "Coordinación de humo",
      iat: ahora,
      exp: ahora + (opciones.expEnSegundos ?? 900),
    })
  );
  const clave = opciones.clavePrivada ?? fs.readFileSync(process.env.HUMO_CLAVE_PRIVADA ?? "", "utf-8");
  const firma = createSign("RSA-SHA256").update(`${cabecera}.${carga}`).sign(clave);
  return `${cabecera}.${carga}.${base64Url(firma)}`;
}

export const bearer = (token: string) => ({ Authorization: `Bearer ${token}` });

/**
 * Deja la credencial donde la deja el botón de Google al volver (`guardarCredencialPendiente`) y abre la
 * elección de organización. A partir de ahí todo es el recorrido real de la aplicación.
 */
export async function iniciarSesion(page: Page, org: OrganizacionHumo): Promise<void> {
  await page.addInitScript((token: string) => {
    if (window.sessionStorage.getItem("humo-sembrado")) return;
    window.sessionStorage.setItem("humo-sembrado", "1");
    window.sessionStorage.setItem("lopdp-credencial-pendiente-v1", token);
  }, firmarToken(org));
  await page.goto("/organizaciones");
  await page.getByRole("button", { name: new RegExp(org.nombre) }).click();
  await page.waitForURL("**/dashboard");
}
