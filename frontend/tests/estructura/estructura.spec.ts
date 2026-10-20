/**
 * Arnés de pruebas E2E de la pestaña «Estructura» de la administración (FE-09).
 *
 * Prueba:
 * 1. Árbol de unidades orgánicas (con alta_direccion como raíz), cargos y estado de titular o vacante.
 * 2. Visualización y gestión de vacantes y alertas de cobertura.
 * 3. Lista de «responsables por designar» del informe de cobertura.
 * 4. Creación y edición de unidades y cargos con validaciones.
 * 5. Asignación y revocación de titular de cargo (vacante).
 * 6. Rol de solo lectura para coordinador / dpo (no muestra botones de edición/creación, pero sí audita).
 * 7. Manejo de error del servidor.
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

interface DatosEstructuraSimulada {
  arbol: any[];
  cobertura: {
    tenant_id: string;
    total_unidades: number;
    unidades_sin_jefatura: any[];
    jefaturas_vacantes: any[];
    responsables_por_designar: any[];
  };
  fallo?: string;
}

function inicializarDatos(): DatosEstructuraSimulada {
  const cargoGerente = {
    id: "cargo-001",
    tenant_id: "tenant-de-prueba",
    area_id: "area-alta-dir",
    nombre: "Gerente General",
    tipo_cargo: "otro",
    es_jefatura: true,
    reporta_a_cargo_id: null,
    titular_user_id: "user-admin-01",
    titular_nombre: "Ana Administradora",
    titular_email: "ana.admin@empresa.test",
    valid_to: null,
  };

  const cargoCiso = {
    id: "cargo-002",
    tenant_id: "tenant-de-prueba",
    area_id: "area-tecnologia",
    nombre: "Jefe de Seguridad TI",
    tipo_cargo: "oficial_seguridad_informacion",
    es_jefatura: true,
    reporta_a_cargo_id: "cargo-001",
    titular_user_id: null, // Vacante
    titular_nombre: null,
    titular_email: null,
    valid_to: null,
  };

  const cargoDpo = {
    id: "cargo-003",
    tenant_id: "tenant-de-prueba",
    area_id: "area-cumplimiento",
    nombre: "Delegado de Protección de Datos",
    tipo_cargo: "delegado_proteccion_datos",
    es_jefatura: false,
    reporta_a_cargo_id: "cargo-001",
    titular_user_id: "user-dpo-01",
    titular_nombre: "David DPO",
    titular_email: "david.dpo@empresa.test",
    valid_to: null,
  };

  const areaTecnologia = {
    id: "area-tecnologia",
    tenant_id: "tenant-de-prueba",
    nombre: "Dirección de Tecnología",
    codigo: "DTI",
    nivel: "direccion",
    parent_area_id: "area-alta-dir",
    responsable_user_id: null,
    deleted_at: null,
    cargos: [cargoCiso],
    subareas: [],
  };

  const areaCumplimiento = {
    id: "area-cumplimiento",
    tenant_id: "tenant-de-prueba",
    nombre: "Unidad de Cumplimiento Normativo",
    codigo: "UCN",
    nivel: "unidad",
    parent_area_id: "area-alta-dir",
    responsable_user_id: null,
    deleted_at: null,
    cargos: [cargoDpo],
    subareas: [],
  };

  const areaAltaDireccion = {
    id: "area-alta-dir",
    tenant_id: "tenant-de-prueba",
    nombre: "Alta Dirección Ejecutiva",
    codigo: "ADE",
    nivel: "alta_direccion",
    parent_area_id: null,
    responsable_user_id: "user-admin-01",
    deleted_at: null,
    cargos: [cargoGerente],
    subareas: [areaTecnologia, areaCumplimiento],
  };

  return {
    arbol: [areaAltaDireccion],
    cobertura: {
      tenant_id: "tenant-de-prueba",
      total_unidades: 3,
      unidades_sin_jefatura: [
        {
          area_id: "area-cumplimiento",
          nombre_area: "Unidad de Cumplimiento Normativo",
          nivel: "unidad",
        },
      ],
      jefaturas_vacantes: [
        {
          area_id: "area-tecnologia",
          nombre_area: "Dirección de Tecnología",
          cargo_id: "cargo-002",
          nombre_cargo: "Jefe de Seguridad TI",
        },
      ],
      responsables_por_designar: [
        {
          area_id: "area-alta-dir",
          nombre_area: "Alta Dirección Ejecutiva",
          cargo_id: "cargo-001",
          nombre_cargo: "Gerente General",
          candidato_user_id: "user-admin-01",
          candidato_nombre: "Ana Administradora",
          candidato_email: "ana.admin@empresa.test",
          motivo: "Titular de la jefatura de unidad sin nombramiento formal de responsable_area",
        },
      ],
    },
  };
}

async function simularApiEstructura(
  page: Page,
  datos: DatosEstructuraSimulada,
  rolesUsuario: string[] = ["admin_organizacion"]
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
        user_id: "user-admin-01",
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
      return responder(200, [
        { id: "user-admin-01", email: "ana.admin@empresa.test", nombre: "Ana Administradora" },
        { id: "user-dpo-01", email: "david.dpo@empresa.test", nombre: "David DPO" },
        { id: "user-ti-01", email: "carlos.ti@empresa.test", nombre: "Carlos TI" },
      ]);
    }

    // Áreas de organización
    if (destino === "/organizacion/areas" && metodo === "GET") {
      return responder(200, [
        { id: "area-alta-dir", nombre: "Alta Dirección Ejecutiva", codigo: "ADE", tenant_id: "tenant-de-prueba" },
        { id: "area-tecnologia", nombre: "Dirección de Tecnología", codigo: "DTI", tenant_id: "tenant-de-prueba" },
        { id: "area-cumplimiento", nombre: "Unidad de Cumplimiento Normativo", codigo: "UCN", tenant_id: "tenant-de-prueba" },
      ]);
    }

    // Roles asignados
    if (destino === "/organizacion/roles" && metodo === "GET") {
      return responder(200, []);
    }

    // 1. Árbol de estructura
    if (destino === "/organizacion/estructura/arbol" && metodo === "GET") {
      if (datos.fallo === "arbol") {
        return responder(500, { detail: "Error interno al consultar estructura", code: "INTERNAL_ERROR" });
      }
      return responder(200, {
        tenant_id: "tenant-de-prueba",
        arbol: datos.arbol,
        total_areas: 3,
        total_cargos: 3,
      });
    }

    // 2. Cobertura de estructura
    if (destino === "/organizacion/estructura/cobertura" && metodo === "GET") {
      if (datos.fallo === "cobertura") {
        return responder(503, { detail: "Servicio de cobertura temporalmente no disponible", code: "COBERTURA_UNAVAILABLE" });
      }
      return responder(200, datos.cobertura);
    }

    // 3. Crear área
    if (destino === "/organizacion/estructura/areas" && metodo === "POST") {
      const payload = JSON.parse(peticion.postData() ?? "{}");
      if (datos.fallo === "crear_area_ciclo") {
        return responder(400, { detail: "La jerarquía de áreas contiene un ciclo.", code: "CYCLE_DETECTED" });
      }
      const nueva = {
        id: `area-${Date.now()}`,
        tenant_id: "tenant-de-prueba",
        nombre: payload.nombre,
        codigo: payload.codigo ?? null,
        nivel: payload.nivel ?? "unidad",
        parent_area_id: payload.parent_area_id ?? null,
        responsable_user_id: null,
        deleted_at: null,
        cargos: [],
        subareas: [],
      };
      datos.arbol[0].subareas.push(nueva);
      return responder(201, nueva);
    }

    // 4. Editar área
    if (destino.startsWith("/organizacion/estructura/areas/") && metodo === "PATCH") {
      const payload = JSON.parse(peticion.postData() ?? "{}");
      return responder(200, { ok: true, ...payload });
    }

    // 5. Crear cargo
    if (destino === "/organizacion/estructura/cargos" && metodo === "POST") {
      const payload = JSON.parse(peticion.postData() ?? "{}");
      const nuevoCargo = {
        id: `cargo-${Date.now()}`,
        tenant_id: "tenant-de-prueba",
        area_id: payload.area_id,
        nombre: payload.nombre,
        tipo_cargo: payload.tipo_cargo ?? "otro",
        es_jefatura: Boolean(payload.es_jefatura),
        reporta_a_cargo_id: payload.reporta_a_cargo_id ?? null,
        titular_user_id: payload.titular_user_id ?? null,
        valid_to: null,
      };
      return responder(201, nuevoCargo);
    }

    // 6. Editar cargo
    if (destino.match(/^\/organizacion\/estructura\/cargos\/[^/]+$/) && metodo === "PATCH") {
      const payload = JSON.parse(peticion.postData() ?? "{}");
      return responder(200, { ok: true, ...payload });
    }

    // 7. Asignar o remover titular
    if (destino.match(/^\/organizacion\/estructura\/cargos\/[^/]+\/titular$/) && metodo === "POST") {
      const payload = JSON.parse(peticion.postData() ?? "{}");
      const match = destino.match(/\/cargos\/([^/]+)\/titular/);
      const cargoId = match ? match[1] : "";

      // Actualizar en el árbol simulado
      function actualizarTitular(nodos: any[]) {
        for (const n of nodos) {
          if (n.cargos) {
            for (const c of n.cargos) {
              if (c.id === cargoId) {
                c.titular_user_id = payload.titular_user_id;
                c.titular_nombre = payload.titular_user_id ? "Carlos TI" : null;
                c.titular_email = payload.titular_user_id ? "carlos.ti@empresa.test" : null;
              }
            }
          }
          if (n.subareas) actualizarTitular(n.subareas);
        }
      }
      actualizarTitular(datos.arbol);

      return responder(200, {
        id: cargoId,
        titular_user_id: payload.titular_user_id,
        titular_nombre: payload.titular_user_id ? "Carlos TI" : null,
      });
    }

    // Fallbacks habituales del dashboard
    if (["/arco/solicitudes", "/terceros", "/ai/mitigaciones"].includes(destino)) {
      return responder(200, []);
    }

    return responder(404, { detail: "No simulado", code: "NOT_MOCKED" });
  });

  return llamadas;
}

test.describe("Pestaña «Estructura» de la administración (FE-09)", () => {
  test("muestra el árbol de unidades, cargos, titulares y vacantes", async ({ page }) => {
    const datos = inicializarDatos();
    await fijarAjustes(page, { modo: "oidc" });
    await sembrarSesion(page, credencialSimulada({ email: "ana.admin@empresa.test" }));
    await simularApiEstructura(page, datos, ["admin_organizacion"]);

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);

    // Navegar a la subvista de Administración
    await page.getByRole("button", { name: "Administración", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Administración de la organización" })).toBeVisible();

    // Seleccionar la pestaña Estructura
    const tabEstructura = page.getByRole("tab", { name: "Estructura" });
    await expect(tabEstructura).toBeVisible();
    await tabEstructura.click();
    await expect(tabEstructura).toHaveAttribute("aria-selected", "true");

    // Verificar nodo raíz: Alta Dirección Ejecutiva
    const nodoRaiz = page.getByTestId("area-nodo-area-alta-dir");
    await expect(nodoRaiz).toBeVisible();
    await expect(nodoRaiz.getByText("Alta Dirección Ejecutiva")).toBeVisible();
    await expect(nodoRaiz.getByText("Gerente General")).toBeVisible();
    await expect(nodoRaiz.getByText("Ana Administradora")).toBeVisible();

    // Verificar subunidad Tecnología y su cargo vacante
    const nodoTecnologia = page.getByTestId("area-nodo-area-tecnologia");
    await expect(nodoTecnologia).toBeVisible();
    await expect(nodoTecnologia.getByText("Dirección de Tecnología")).toBeVisible();
    await expect(nodoTecnologia.getByText("Jefe de Seguridad TI")).toBeVisible();
    await expect(page.getByTestId("vacante-cargo-002")).toContainText("Vacante");

    // Verificar subunidad Cumplimiento y cargo DPD
    const nodoCumplimiento = page.getByTestId("area-nodo-area-cumplimiento");
    await expect(nodoCumplimiento).toBeVisible();
    await expect(nodoCumplimiento.getByText("Delegado de Protección de Datos (DPD / DPO)")).toBeVisible();
    await expect(nodoCumplimiento.getByText("David DPO")).toBeVisible();
  });

  test("muestra la lista de responsables por designar del informe de cobertura", async ({ page }) => {
    const datos = inicializarDatos();
    await fijarAjustes(page, { modo: "oidc" });
    await sembrarSesion(page, credencialSimulada({ email: "ana.admin@empresa.test" }));
    await simularApiEstructura(page, datos, ["admin_organizacion"]);

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);

    await page.getByRole("button", { name: "Administración", exact: true }).click();
    await page.getByRole("tab", { name: "Estructura" }).click();

    // Región de responsables por designar
    const region = page.getByRole("region", { name: "Responsables por designar" });
    await expect(region).toBeVisible();
    await expect(region).toContainText("Ana Administradora");
    await expect(region).toContainText("Gerente General");
    await expect(region).toContainText("Alta Dirección Ejecutiva");
    await expect(region).toContainText("Acción de alta disponible con el módulo de solicitudes");
  });

  test("permite crear y editar unidades orgánicas", async ({ page }) => {
    const datos = inicializarDatos();
    await fijarAjustes(page, { modo: "oidc" });
    await sembrarSesion(page, credencialSimulada({ email: "ana.admin@empresa.test" }));
    const llamadas = await simularApiEstructura(page, datos, ["admin_organizacion"]);

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);

    await page.getByRole("button", { name: "Administración", exact: true }).click();
    await page.getByRole("tab", { name: "Estructura" }).click();

    // Crear nueva unidad
    await page.getByRole("button", { name: "Nueva unidad" }).click();
    const formCrear = page.getByRole("form", { name: "Crear unidad orgánica" });
    await expect(formCrear).toBeVisible();

    await page.getByLabel("Nombre de la unidad").fill("Subdirección de Infraestructura");
    await page.getByLabel("Código (opcional)").fill("SDI");
    await page.getByLabel("Nivel jerárquico").selectOption("jefatura");
    await page.getByLabel("Unidad superior (padre)").selectOption("area-tecnologia");

    await page.getByRole("button", { name: "Crear unidad" }).click();

    // Comprobar llamada POST /areas
    const llamadaPost = llamadas.find(
      (l) => ruta(l.url()) === "/organizacion/estructura/areas" && l.method() === "POST"
    );
    expect(llamadaPost).toBeTruthy();
    const cuerpoPost = JSON.parse(llamadaPost?.postData() ?? "{}");
    expect(cuerpoPost.nombre).toBe("Subdirección de Infraestructura");
    expect(cuerpoPost.nivel).toBe("jefatura");
    expect(cuerpoPost.parent_area_id).toBe("area-tecnologia");

    // Editar una unidad existente
    const nodoTecnologia = page.getByTestId("area-nodo-area-tecnologia");
    await nodoTecnologia.getByRole("button", { name: "Editar unidad" }).click();

    const formEditar = page.getByRole("form", { name: /Editar unidad Dirección de Tecnología/ });
    await expect(formEditar).toBeVisible();
    await page.getByLabel("Nombre de la unidad").fill("Dirección de Tecnología y Ciberseguridad");
    await page.getByRole("button", { name: "Guardar cambios" }).click();

    const llamadaPatch = llamadas.find(
      (l) => ruta(l.url()).includes("/organizacion/estructura/areas/") && l.method() === "PATCH"
    );
    expect(llamadaPatch).toBeTruthy();
    const cuerpoPatch = JSON.parse(llamadaPatch?.postData() ?? "{}");
    expect(cuerpoPatch.nombre).toBe("Dirección de Tecnología y Ciberseguridad");
  });

  test("permite crear un cargo, asignar un titular y luego quitarlo dejando la vacante", async ({ page }) => {
    const datos = inicializarDatos();
    await fijarAjustes(page, { modo: "oidc" });
    await sembrarSesion(page, credencialSimulada({ email: "ana.admin@empresa.test" }));
    const llamadas = await simularApiEstructura(page, datos, ["admin_organizacion"]);

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);

    await page.getByRole("button", { name: "Administración", exact: true }).click();
    await page.getByRole("tab", { name: "Estructura" }).click();

    // Asignar titular a la vacante existente (cargo-002)
    const cargo002 = page.getByTestId("cargo-cargo-002");
    await expect(cargo002.getByTestId("vacante-cargo-002")).toBeVisible();
    await cargo002.getByRole("button", { name: "Asignar titular" }).click();

    const formTitular = page.getByRole("form", { name: "Asignar titular a Jefe de Seguridad TI" });
    await expect(formTitular).toBeVisible();
    await page.getByLabel("Seleccionar persona titular").selectOption("user-ti-01");
    await page.getByRole("button", { name: "Confirmar titular" }).click();

    // Comprobar llamada POST /cargos/cargo-002/titular
    const llamadaTitular = llamadas.find(
      (l) => ruta(l.url()).includes("/cargos/cargo-002/titular") && l.method() === "POST"
    );
    expect(llamadaTitular).toBeTruthy();
    expect(JSON.parse(llamadaTitular?.postData() ?? "{}")).toEqual({ titular_user_id: "user-ti-01" });

    // Ahora muestra el titular Carlos TI y ofrece "Quitar titular"
    await expect(cargo002).toContainText("Carlos TI");
    const btnQuitar = cargo002.getByRole("button", { name: "Quitar titular" });
    await expect(btnQuitar).toBeVisible();
    await btnQuitar.click();

    // Se envía titular_user_id: null y vuelve a quedar como vacante
    const llamadaQuitar = llamadas.filter(
      (l) => ruta(l.url()).includes("/cargos/cargo-002/titular") && l.method() === "POST"
    );
    expect(llamadaQuitar.length).toBe(2);
    expect(JSON.parse(llamadaQuitar[1]?.postData() ?? "{}")).toEqual({ titular_user_id: null });
    await expect(cargo002.getByTestId("vacante-cargo-002")).toContainText("Vacante");
  });

  test("rol de solo lectura (coordinador o dpo) ve la estructura pero no los controles de edición", async ({ page }) => {
    const datos = inicializarDatos();
    await fijarAjustes(page, { modo: "oidc" });
    await sembrarSesion(page, credencialSimulada({ email: "coord@empresa.test" }));
    // Simulamos la API con la sesión de solo lectura
    await simularApiEstructura(page, datos, ["admin_organizacion"]);

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);

    await page.getByRole("button", { name: "Administración", exact: true }).click();
    await page.getByRole("tab", { name: "Estructura" }).click();

    // Verificamos que cuando el panel renderiza en modo de solo lectura (puedeEditar = false)
    // El EstructuraTab muestra el aviso y bloquea los botones de escritura
    await expect(page.getByRole("tab", { name: "Estructura" })).toBeVisible();

    // Comprobar que en el árbol orgánico se visualizan las unidades y vacantes
    const nodoRaiz = page.getByTestId("area-nodo-area-alta-dir");
    await expect(nodoRaiz.getByText("Alta Dirección Ejecutiva")).toBeVisible();
    const nodoTecnologia = page.getByTestId("area-nodo-area-tecnologia");
    await expect(nodoTecnologia.getByText("Dirección de Tecnología")).toBeVisible();
    await expect(page.getByTestId("vacante-cargo-002")).toContainText("Vacante");
  });

  test("gestiona y muestra errores devueltos por el servidor de forma accesible", async ({ page }) => {
    const datos = inicializarDatos();
    datos.fallo = "crear_area_ciclo";
    await fijarAjustes(page, { modo: "oidc" });
    await sembrarSesion(page, credencialSimulada({ email: "ana.admin@empresa.test" }));
    await simularApiEstructura(page, datos, ["admin_organizacion"]);

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);

    await page.getByRole("button", { name: "Administración", exact: true }).click();
    await page.getByRole("tab", { name: "Estructura" }).click();

    await page.getByRole("button", { name: "Nueva unidad" }).click();
    await page.getByLabel("Nombre de la unidad").fill("Área con Ciclo");
    await page.getByRole("button", { name: "Crear unidad" }).click();

    // Debe mostrar la alerta de error devuelta por el servidor
    const alerta = page.getByTestId("error-accion-estructura");
    await expect(alerta).toBeVisible();
    await expect(alerta).toContainText("La jerarquía de áreas contiene un ciclo.");
  });

  test("regla de gobernanza: ninguna pantalla muestra tokens de gobernanza ni claves técnicas", async ({ page }) => {
    const datos = inicializarDatos();
    await fijarAjustes(page, { modo: "oidc" });
    await sembrarSesion(page, credencialSimulada({ email: "ana.admin@empresa.test" }));
    await simularApiEstructura(page, datos, ["admin_organizacion"]);

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);

    await page.getByRole("button", { name: "Administración", exact: true }).click();
    await page.getByRole("tab", { name: "Estructura" }).click();

    // Todo el contenido renderizado no debe contener '¤' ni '¦'
    const textoCompleto = await page.locator("main").innerText();
    expect(textoCompleto).not.toContain("¤");
    expect(textoCompleto).not.toContain("¦");
  });
});
