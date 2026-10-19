/**
 * Helper de base de datos para pruebas de integración contra backend real (TEST-03).
 * Ejecuta comandos SQL de forma determinista usando el Python del sistema con psycopg.
 */
import { spawnSync } from "child_process";
import * as path from "path";

const SCRIPT_PYTHON = `
import sys, json, psycopg

url = sys.argv[1]
queries = json.loads(sys.argv[2])

with psycopg.connect(url) as conn:
    with conn.cursor() as cur:
        for item in queries:
            sql = item[0]
            params = item[1] if len(item) > 1 else None
            cur.execute(sql, params)
        conn.commit()
print("OK")
`;

export function resolverTestDatabaseUrl(): string {
  if (process.env.TEST_DATABASE_URL && process.env.TEST_DATABASE_URL.trim()) {
    return process.env.TEST_DATABASE_URL.trim();
  }
  const fs = require("fs");
  const archivoRama = "C:\\Users\\Juan Carlos\\Desktop\\herramientas\\rama-test-rm07.txt";
  if (fs.existsSync(archivoRama)) {
    const contenido = fs.readFileSync(archivoRama, "utf-8");
    for (const linea of contenido.split("\n")) {
      const match = linea.match(/^\s*TEST_DATABASE_URL\s*=\s*(.+)$/);
      if (match) {
        return match[1].trim();
      }
    }
  }
  return "";
}

export function ejecutarSql(queries: Array<[string, Record<string, any> | Array<any>]>): void {
  const dbUrl = resolverTestDatabaseUrl();
  if (!dbUrl) {
    throw new Error("TEST_DATABASE_URL no está configurada");
  }
  const normalizedUrl = dbUrl.replace(/^postgresql\+psycopg:\/\//, "postgresql://");

  const proc = spawnSync("python", ["-c", SCRIPT_PYTHON, normalizedUrl, JSON.stringify(queries)], {
    encoding: "utf-8",
  });

  if (proc.status !== 0 || !proc.stdout.includes("OK")) {
    throw new Error(
      `Fallo al ejecutar SQL en base de datos de pruebas:\nSTDOUT: ${proc.stdout}\nSTDERR: ${proc.stderr}`
    );
  }
}

export interface TenantFixture {
  tenantId: string;
  adminUserId: string;
  userEmail: string;
  domain: string;
}

export function crearTenantConAdmin(prefijo = "test-int"): TenantFixture {
  const sufijo = Math.random().toString(36).substring(2, 9);
  const tenantId = `org-${prefijo}-${sufijo}`;
  const adminUserId = `user-admin-${sufijo}`;
  const domain = `${tenantId}.test`;
  const userEmail = `admin@${domain}`;

  ejecutarSql([
    [
      "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano, activo) VALUES (%s, %s, %s, %s, %s, true)",
      [tenantId, `Org ${tenantId}`, `Org ${tenantId} S.A.`, `RUC${sufijo}001`, null],
    ],
    [
      "INSERT INTO users (id, email, nombre) VALUES (%s, %s, %s)",
      [adminUserId, userEmail, "Administrador Test"],
    ],
    [
      "INSERT INTO users (id, email, nombre) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
      ["user-demo-implementador", "demo@test.ec", "Usuario Demo Implementador"],
    ],
    [
      "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (%s, %s, %s, %s)",
      [`utr-${sufijo}`, adminUserId, tenantId, "admin_organizacion"],
    ],
    [
      "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (%s, %s, %s, %s)",
      [`utr-demo-${sufijo}`, "user-demo-implementador", tenantId, "admin_organizacion"],
    ],
  ]);

  return {
    tenantId,
    adminUserId,
    userEmail,
    domain,
  };
}

export function limpiarTenant(tenantId: string, domain: string): void {
  ejecutarSql([
    ["DELETE FROM audit_events WHERE tenant_id = %s", [tenantId]],
    ["DELETE FROM user_tenant_roles WHERE tenant_id = %s", [tenantId]],
    ["DELETE FROM areas WHERE tenant_id = %s", [tenantId]],
    ["DELETE FROM users WHERE email LIKE %s", [`%@${domain}`]],
    ["DELETE FROM tenants WHERE id = %s", [tenantId]],
  ]);
}
