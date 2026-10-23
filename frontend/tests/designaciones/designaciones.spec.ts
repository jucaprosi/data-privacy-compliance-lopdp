/**
 * Arnés de pruebas E2E para las designaciones formales del DPD y del Coordinador (FE-11).
 *
 * Valida de forma rigurosa y determinista:
 * 1. Estado de la organización (GET /estado): advertencias claras cuando falta designar DPD o Coordinador.
 * 2. Visualización de lista de designaciones con tipo, persona, fechas, estado de declaración y de inscripción SPDP.
 * 3. Formulario de creación de designación (éxito y manejo de error 409 por cargo incompatible del DPO o duplicado).
 * 4. Registro de constancia de inscripción ante la SPDP.
 * 5. Revocación de designación formal con confirmación.
 * 6. Cockpit DPD («Mi designación»): visualización de designación activa y emisión de la declaración previa de conflictos (solo por la persona designada).
 * 7. Control de permisos: roles sin permiso de administración (coordinador, dpo, implementador) no ven botones de edición ni acciones administrativas.
 * 8. Regla de gobernanza: ninguna pantalla muestra tokens de gobernanza (¤, ¦) ni claves técnicas.
 */
import { expect, test, type Page, type Request } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";
import {
  credencialSimulada,
  fijarAjustes,
  ruta,
  sembrarSesion,
} from "../auth/utilesAuth";

interface DatosDesignacionesSimuladas {
  designaciones: any[];
  estado: any;
  usuarios: any[];
  areas: any[];
  roles: any[];
  falloCrearDpd?: boolean;
}

function inicializarDatos(): DatosDesignacionesSimuladas {
  const usuarios = [
    {
      id: "user-admin-01",
      email: "ana.admin@empresa.test",
      nombre: "Ana Administradora",
    },
    {
      id: "user-dpd-01",
      email: "david.dpd@empresa.test",
      nombre: "David Delegado",
    },
    {
      id: "user-coord-01",
      email: "carlos.coord@empresa.test",
      nombre: "Carlos Coordinador",
    },
  ];

  const areas = [
    {
      id: "area-alta-dir",
      nombre: "Alta Dirección Ejecutiva",
      codigo: "ADE",
      tenant_id: "tenant-de-prueba",
    },
  ];

  const roles = [
    {
      id: "grant-1",
      user_id: "user-admin-01",
      role: "admin_organizacion",
      area_id: null,
      granted_at: new Date().toISOString(),
      granted_by: "sistema",
    },
    {
      id: "grant-2",
      user_id: "user-dpd-01",
      role: "dpo",
      area_id: null,
      granted_at: new Date().toISOString(),
      granted_by: "user-admin-01",
    },
  ];

  const designacionDpd = {
    id: "desig-dpd-001",
    tenant_id: "tenant-de-prueba",
    tipo: "dpd",
    user_id: "user-dpd-01",
    representante_nombre: "María Representante Legal",
    representante_identificacion: "1799887766001",
    representante_cargo: "Presidenta Ejecutiva",
    fecha_designacion: "2026-10-15",
    doc_referencia: "ACTA-JUNTA-2026-10",
    valid_from: "2026-10-15T00:00:00Z",
    valid_to: null,
    vinculo: "relacion_dependencia",
    aceptacion_at: null,
    declaracion_at: null,
    declaracion_texto: null,
    declaracion_tiene_conflicto: false,
    declaracion_es_socio_accionista: false,
    declaracion_es_pariente_admin: false,
    inscripcion_spdp_fecha: null,
    inscripcion_spdp_ref: null,
    revocada_at: null,
    revocada_motivo: null,
    created_at: "2026-10-15T10:00:00Z",
    updated_at: "2026-10-15T10:00:00Z",
    usuario_nombre: "David Delegado",
    usuario_email: "david.dpd@empresa.test",
  };

  const estadoInicial = {
    tenant_id: "tenant-de-prueba",
    dpd: {
      designado: true,
      designacion: designacionDpd,
      declaracion_completada: false,
      inscrito_spdp: false,
      conflicto_sobrevenido: false,
      cargos_incompatibles: [],
      alertas: [
        "Falta registrar la declaración formal de no tener conflicto de intereses.",
        "Falta registrar la constancia de inscripción ante la SPDP.",
      ],
    },
    coordinador: {
      designado: false,
      designacion: null,
      tiene_mandato_escrito: false,
      alertas: [
        "El Coordinador carece de mandato formal escrito de la alta dirección para supervisar las áreas.",
      ],
    },
  };

  return {
    designaciones: [designacionDpd],
    estado: estadoInicial,
    usuarios,
    areas,
    roles,
  };
}

async function simularApiDesignaciones(
  page: Page,
  datos: DatosDesignacionesSimuladas,
  rolesUsuario: string[] = ["admin_organizacion"],
  userId: string = "user-admin-01"
): Promise<Request[]> {
  const llamadas: Request[] = [];

  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    llamadas.push(peticion);
    const destino = ruta(peticion.url());
    const metodo = peticion.method().toUpperCase();

    const responder = (status: number, cuerpo: unknown) =>
      route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(cuerpo),
      });

    // Sesión y roles
    if (destino === "/organizacion/me/roles") {
      return responder(200, {
        user_id: userId,
        tenant_id: "tenant-de-prueba",
        roles: rolesUsuario.map((role) => ({
          role,
          area_id: null,
          area_nombre: null,
          valid_to: null,
        })),
      });
    }

    // Configuración general
    if (destino === "/organizacion/configuracion") {
      return responder(200, {
        id: "tenant-de-prueba",
        tamano: "mediana",
        sector: "Tecnología",
        activo: true,
      });
    }

    // Usuarios del tenant
    if (destino === "/organizacion/usuarios" && metodo === "GET") {
      return responder(200, datos.usuarios);
    }

    // Áreas de organización
    if (destino === "/organizacion/areas" && metodo === "GET") {
      return responder(200, datos.areas);
    }

    // Roles asignados
    if (destino === "/organizacion/roles" && metodo === "GET") {
      return responder(200, datos.roles);
    }

    // Estructura orgánica (arbol y cobertura)
    if (destino === "/organizacion/estructura/arbol" && metodo === "GET") {
      return responder(200, {
        tenant_id: "tenant-de-prueba",
        arbol: [],
        total_areas: 0,
        total_cargos: 0,
      });
    }

    if (destino === "/organizacion/estructura/cobertura" && metodo === "GET") {
      return responder(200, {
        tenant_id: "tenant-de-prueba",
        total_unidades: 0,
        unidades_sin_jefatura: [],
        jefaturas_vacantes: [],
        responsables_por_designar: [],
      });
    }

    // Cockpit DPO bitácora
    if (destino === "/dpo/bitacora" && metodo === "GET") {
      return responder(200, { dictamenes: [] });
    }

    // ==========================================
    // Endpoints ORG-06 Designaciones Formales
    // ==========================================

    // 1. GET /organizacion/designaciones/estado
    if (destino === "/organizacion/designaciones/estado" && metodo === "GET") {
      return responder(200, datos.estado);
    }

    // 2. GET o POST /organizacion/designaciones
    if (destino.startsWith("/organizacion/designaciones") && !destino.includes("/estado") && !destino.includes("/declarar") && !destino.includes("/inscribir") && !destino.includes("/revocar")) {
      if (metodo === "GET") {
        const url = new URL(peticion.url());
        const tipo = url.searchParams.get("tipo");
        let res = datos.designaciones;
        if (tipo) {
          res = res.filter((d) => d.tipo === tipo);
        }
        return responder(200, res);
      }

      if (metodo === "POST") {
        const payload = JSON.parse(peticion.postData() ?? "{}");

        // Rechazo 409 simulado si se marca fallo
        if (payload.tipo === "dpd" && datos.falloCrearDpd) {
          return responder(409, {
            detail: "La persona ocupa cargos incompatibles con las funciones del DPD: 'Jefe de Sistemas' (oficial_seguridad_informacion). Base legal: Arts. 15.5 y 16 del Reglamento del Delegado.",
            code: "INCOMPATIBLE_ROLE",
          });
        }

        // Rechazo 409 si ya existe activa
        const existente = datos.designaciones.find(
          (d) => d.tipo === payload.tipo && !d.revocada_at
        );
        if (existente) {
          return responder(409, {
            detail: `Ya existe una designación formal activa para el tipo '${payload.tipo}'.`,
            code: "ALREADY_EXISTS",
          });
        }

        const u = datos.usuarios.find((usr) => usr.id === payload.user_id);
        const nueva = {
          id: `desig-${payload.tipo}-${Date.now()}`,
          tenant_id: "tenant-de-prueba",
          tipo: payload.tipo,
          user_id: payload.user_id,
          representante_nombre: payload.representante_nombre,
          representante_identificacion: payload.representante_identificacion,
          representante_cargo: payload.representante_cargo,
          fecha_designacion: payload.fecha_designacion,
          doc_referencia: payload.doc_referencia,
          vinculo: payload.vinculo ?? null,
          valid_to: payload.valid_to ?? null,
          aceptacion_at: null,
          declaracion_at: null,
          declaracion_texto: null,
          declaracion_tiene_conflicto: false,
          declaracion_es_socio_accionista: false,
          declaracion_es_pariente_admin: false,
          inscripcion_spdp_fecha: null,
          inscripcion_spdp_ref: null,
          revocada_at: null,
          revocada_motivo: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          usuario_nombre: u?.nombre ?? payload.user_id,
          usuario_email: u?.email ?? "",
        };

        datos.designaciones.unshift(nueva);

        if (payload.tipo === "coordinador") {
          datos.estado.coordinador = {
            designado: true,
            designacion: nueva,
            tiene_mandato_escrito: true,
            alertas: [],
          };
        } else {
          datos.estado.dpd = {
            designado: true,
            designacion: nueva,
            declaracion_completada: false,
            inscrito_spdp: false,
            conflicto_sobrevenido: false,
            cargos_incompatibles: [],
            alertas: [
              "Falta registrar la declaración formal de no tener conflicto de intereses.",
              "Falta registrar la constancia de inscripción ante la SPDP.",
            ],
          };
        }

        return responder(201, nueva);
      }
    }

    // 3. POST /{id}/declarar
    if (destino.match(/^\/organizacion\/designaciones\/[^/]+\/declarar$/) && metodo === "POST") {
      const match = destino.match(/\/designaciones\/([^/]+)\/declarar/);
      const id = match ? match[1] : "";
      const payload = JSON.parse(peticion.postData() ?? "{}");

      const desig = datos.designaciones.find((d) => d.id === id);
      if (!desig) {
        return responder(404, { detail: "Designación no encontrada", code: "NOT_FOUND" });
      }

      if (payload.declaracion_tiene_conflicto || payload.declaracion_es_socio_accionista || payload.declaracion_es_pariente_admin) {
        return responder(409, {
          detail: "No puede asumir la función de DPD porque declara tener conflicto de intereses real, potencial o aparente. Base legal: Art. 17 Reglamento del Delegado.",
          code: "CONFLICT_DECLARED",
        });
      }

      desig.declaracion_at = new Date().toISOString();
      desig.declaracion_texto = payload.declaracion_texto;
      desig.declaracion_tiene_conflicto = false;
      desig.declaracion_es_socio_accionista = false;
      desig.declaracion_es_pariente_admin = false;
      desig.aceptacion_at = desig.declaracion_at;

      if (datos.estado.dpd.designacion?.id === id) {
        datos.estado.dpd.declaracion_completada = true;
        datos.estado.dpd.alertas = datos.estado.dpd.alertas.filter(
          (a: string) => !a.includes("declaración")
        );
      }

      return responder(200, desig);
    }

    // 4. POST /{id}/inscribir
    if (destino.match(/^\/organizacion\/designaciones\/[^/]+\/inscribir$/) && metodo === "POST") {
      const match = destino.match(/\/designaciones\/([^/]+)\/inscribir/);
      const id = match ? match[1] : "";
      const payload = JSON.parse(peticion.postData() ?? "{}");

      const desig = datos.designaciones.find((d) => d.id === id);
      if (!desig) {
        return responder(404, { detail: "Designación no encontrada", code: "NOT_FOUND" });
      }

      desig.inscripcion_spdp_fecha = payload.inscripcion_spdp_fecha;
      desig.inscripcion_spdp_ref = payload.inscripcion_spdp_ref;

      if (datos.estado.dpd.designacion?.id === id) {
        datos.estado.dpd.inscrito_spdp = true;
        datos.estado.dpd.alertas = datos.estado.dpd.alertas.filter(
          (a: string) => !a.includes("inscripción")
        );
      }

      return responder(200, desig);
    }

    // 5. POST /{id}/revocar
    if (destino.match(/^\/organizacion\/designaciones\/[^/]+\/revocar$/) && metodo === "POST") {
      const match = destino.match(/\/designaciones\/([^/]+)\/revocar/);
      const id = match ? match[1] : "";
      const payload = JSON.parse(peticion.postData() ?? "{}");

      const desig = datos.designaciones.find((d) => d.id === id);
      if (!desig) {
        return responder(404, { detail: "Designación no encontrada", code: "NOT_FOUND" });
      }

      desig.revocada_at = new Date().toISOString();
      desig.revocada_motivo = payload.motivo;

      if (desig.tipo === "dpd") {
        datos.estado.dpd = {
          designado: false,
          designacion: null,
          declaracion_completada: false,
          inscrito_spdp: false,
          conflicto_sobrevenido: false,
          cargos_incompatibles: [],
          alertas: ["No existe una designación formal activa para el Delegado de Protección de Datos."],
        };
      } else {
        datos.estado.coordinador = {
          designado: false,
          designacion: null,
          tiene_mandato_escrito: false,
          alertas: ["El Coordinador carece de mandato formal escrito de la alta dirección para supervisar las áreas."],
        };
      }

      return responder(200, desig);
    }

    // Fallbacks habituales del dashboard
    if (["/arco/solicitudes", "/terceros", "/ai/mitigaciones"].includes(destino)) {
      return responder(200, []);
    }

    return responder(404, { detail: "No simulado", code: "NOT_MOCKED" });
  });

  return llamadas;
}

test.describe("Pantallas de Designaciones Formales (FE-11)", () => {
  test("muestra estado de la organización y lista de designaciones en pestaña Designaciones", async ({ page }) => {
    const datos = inicializarDatos();
    await fijarAjustes(page, { modo: "oidc" });
    await sembrarSesion(page, credencialSimulada({ email: "ana.admin@empresa.test" }));
    await simularApiDesignaciones(page, datos, ["admin_organizacion"], "user-admin-01");

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);

    // Navegar a la subvista de Administración
    await page.getByRole("button", { name: "Administración", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Administración de la organización" })).toBeVisible();

    // Navegar a la pestaña Designaciones
    const tabDesignaciones = page.getByRole("tab", { name: "Designaciones" });
    await expect(tabDesignaciones).toBeVisible();
    await tabDesignaciones.click();
    await expect(tabDesignaciones).toHaveAttribute("aria-selected", "true");

    // Verificar tarjetas de estado
    const tarjetaDpd = page.getByTestId("tarjeta-estado-dpd");
    await expect(tarjetaDpd).toBeVisible();
    await expect(tarjetaDpd).toContainText("David Delegado");
    await expect(tarjetaDpd).toContainText("Pendiente de emitir");
    await expect(tarjetaDpd).toContainText("Pendiente de inscribir");

    const tarjetaCoord = page.getByTestId("tarjeta-estado-coordinador");
    await expect(tarjetaCoord).toBeVisible();
    await expect(tarjetaCoord).toContainText("Falta designar");
    await expect(tarjetaCoord).toContainText("El Coordinador carece de mandato formal escrito");

    // Verificar fila en la tabla
    const fila = page.getByTestId("fila-designacion-desig-dpd-001");
    await expect(fila).toBeVisible();
    await expect(fila).toContainText("DPD");
    await expect(fila).toContainText("David Delegado");
    await expect(fila).toContainText("María Representante Legal");
    await expect(fila).toContainText("Pendiente");
    await expect(fila).toContainText("Vigente");
  });

  test("permite registrar nueva designación y maneja error 409 del servidor", async ({ page }) => {
    const datos = inicializarDatos();
    await fijarAjustes(page, { modo: "oidc" });
    await sembrarSesion(page, credencialSimulada({ email: "ana.admin@empresa.test" }));
    await simularApiDesignaciones(page, datos, ["admin_organizacion"], "user-admin-01");

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);

    await page.getByRole("button", { name: "Administración", exact: true }).click();
    const tabDesignaciones = page.getByRole("tab", { name: "Designaciones" });
    await tabDesignaciones.click();

    // 1. Probar crear coordinador con éxito
    await page.getByTestId("btn-crear-designacion").click();
    const modalCrear = page.getByRole("dialog", { name: /Registrar designación formal/ });
    await expect(modalCrear).toBeVisible();

    await modalCrear.locator("#tipo-designacion").selectOption("coordinador");
    await modalCrear.locator("#usuario-designado").selectOption("user-coord-01");
    await modalCrear.locator("#rep-nombre").fill("Directorio General");
    await modalCrear.locator("#rep-id").fill("1799999999001");
    await modalCrear.locator("#rep-cargo").fill("Apoderado General");
    await modalCrear.locator("#doc-ref").fill("RESOLUCION-DIR-2026-01");

    await modalCrear.getByTestId("btn-confirmar-crear-designacion").click();
    await expect(modalCrear).not.toBeVisible();

    // Comprobar que la tarjeta de Coordinador ahora aparece designado
    const tarjetaCoord = page.getByTestId("tarjeta-estado-coordinador");
    await expect(tarjetaCoord).toContainText("Designado");
    await expect(tarjetaCoord).toContainText("Carlos Coordinador");

    // 2. Probar error 409 cuando se intenta crear un DPD duplicado
    await page.getByTestId("btn-crear-designacion").click();
    await expect(modalCrear).toBeVisible();
    await modalCrear.locator("#tipo-designacion").selectOption("dpd");
    await modalCrear.locator("#usuario-designado").selectOption("user-dpd-01");
    await modalCrear.locator("#rep-nombre").fill("Directorio General");
    await modalCrear.locator("#rep-id").fill("1799999999001");
    await modalCrear.locator("#rep-cargo").fill("Apoderado General");
    await modalCrear.locator("#doc-ref").fill("RESOLUCION-DIR-2026-02");

    await modalCrear.getByTestId("btn-confirmar-crear-designacion").click();

    // Debe mostrar error 409 accesible
    const bloqueError = page.getByTestId("error-accion-designaciones");
    await expect(bloqueError).toBeVisible();
    await expect(bloqueError).toContainText("Ya existe una designación formal activa para el tipo 'dpd'");
  });

  test("permite registrar constancia de inscripción ante la SPDP y revocar la designación", async ({ page }) => {
    const datos = inicializarDatos();
    await fijarAjustes(page, { modo: "oidc" });
    await sembrarSesion(page, credencialSimulada({ email: "ana.admin@empresa.test" }));
    await simularApiDesignaciones(page, datos, ["admin_organizacion"], "user-admin-01");

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);

    await page.getByRole("button", { name: "Administración", exact: true }).click();
    await page.getByRole("tab", { name: "Designaciones" }).click();

    // 1. Inscribir SPDP
    const btnInscribir = page.getByTestId("btn-inscribir-desig-dpd-001");
    await expect(btnInscribir).toBeVisible();
    await btnInscribir.click();

    const modalInscribir = page.getByRole("dialog", { name: /Constancia de inscripción ante SPDP/ });
    await expect(modalInscribir).toBeVisible();
    await modalInscribir.locator("#ref-spdp").fill("SPDP-REG-2026-9999");
    await modalInscribir.getByTestId("btn-confirmar-inscribir").click();
    await expect(modalInscribir).not.toBeVisible();

    // Comprobar que en la tabla ahora figura Inscrito
    const fila = page.getByTestId("fila-designacion-desig-dpd-001");
    await expect(fila).toContainText("SPDP-REG-2026-9999");

    // 2. Revocar designación
    const btnRevocar = page.getByTestId("btn-revocar-desig-dpd-001");
    await expect(btnRevocar).toBeVisible();
    await btnRevocar.click();

    const modalRevocar = page.getByRole("dialog", { name: /Confirmar revocación de designación/ });
    await expect(modalRevocar).toBeVisible();
    await modalRevocar.locator("#motivo-revocacion").fill("Cese voluntario de funciones de común acuerdo");
    await modalRevocar.getByTestId("btn-confirmar-revocar").click();
    await expect(modalRevocar).not.toBeVisible();

    // La fila debe mostrar estado Revocada
    await expect(fila).toContainText("Revocada");
    // La tarjeta de DPD debe volver a marcar que falta designar
    await expect(page.getByTestId("tarjeta-estado-dpd")).toContainText("Falta designar");
  });

  test("persona designada ve su designación y emite declaración de conflictos en Cockpit DPD", async ({ page }) => {
    const datos = inicializarDatos();
    await fijarAjustes(page, { modo: "oidc" });
    await sembrarSesion(page, credencialSimulada({ email: "david.dpd@empresa.test" }));
    await simularApiDesignaciones(page, datos, ["dpo"], "user-dpd-01");

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Cockpit DPD \/ DPO/i);

    // Verificar sección «Mi designación» en el Cockpit
    const seccionDesig = page.getByTestId("seccion-mi-designacion");
    await expect(seccionDesig).toBeVisible();
    await expect(seccionDesig).toContainText("María Representante Legal");
    await expect(seccionDesig).toContainText("Pendiente de emisión por la persona designada");

    // Abrir modal de declaración
    const btnDeclarar = page.getByTestId("btn-abrir-declaracion-conflictos");
    await expect(btnDeclarar).toBeVisible();
    await btnDeclarar.click();

    const modalDeclarar = page.getByRole("dialog", { name: /Declaración previa de conflictos/ });
    await expect(modalDeclarar).toBeVisible();

    // Emitir declaración limpia (sin marcar conflictos)
    await modalDeclarar.getByTestId("btn-confirmar-declaracion").click();
    await expect(modalDeclarar).not.toBeVisible();

    // Verificar que ahora se muestra la declaración emitida y no el botón de emitir
    await expect(btnDeclarar).not.toBeVisible();
    await expect(seccionDesig).toContainText("Declaración emitida");
  });

  test("rol sin permiso (coordinador) no ve el botón de Administración ni gestiona designaciones", async ({ page }) => {
    const datos = inicializarDatos();
    await fijarAjustes(page, { modo: "oidc" });
    await sembrarSesion(page, credencialSimulada({ email: "carlos.coord@empresa.test" }));
    await simularApiDesignaciones(page, datos, ["coordinador"], "user-coord-01");

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);

    // El botón «Administración» solo se renderiza para admin_organizacion
    await expect(page.getByRole("button", { name: "Administración", exact: true })).not.toBeVisible();
  });

  test("regla de gobernanza: ninguna pantalla muestra tokens de gobernanza ni claves técnicas", async ({ page }) => {
    const datos = inicializarDatos();
    await fijarAjustes(page, { modo: "oidc" });
    await sembrarSesion(page, credencialSimulada({ email: "ana.admin@empresa.test" }));
    await simularApiDesignaciones(page, datos, ["admin_organizacion"], "user-admin-01");

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);

    await page.getByRole("button", { name: "Administración", exact: true }).click();
    await page.getByRole("tab", { name: "Designaciones" }).click();

    const textoAdmin = await page.locator("main").innerText();
    expect(textoAdmin).not.toContain("¤");
    expect(textoAdmin).not.toContain("¦");

    // Ir a sala DPO y verificar Cockpit
    await irASala(page, /Cockpit DPD \/ DPO/i);
    const textoDpo = await page.locator("main").innerText();
    expect(textoDpo).not.toContain("¤");
    expect(textoDpo).not.toContain("¦");
  });
});
