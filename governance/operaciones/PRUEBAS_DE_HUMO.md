# Pruebas de humo de extremo a extremo
`¤ci-cd` `¤arbitro`

> Compuerta de fallo rápido del CI. Corre antes del arnés de Pytest y de Playwright: si falla, esos trabajos no arrancan. Si pasa, la suite completa sigue siendo obligatoria. El humo nunca reemplaza a la suite.

Árbitro de estas reglas: `tests/test_servidor_humo.py`.

---

## 1. Qué es

Next.js de producción (`next build` + `next start`) y FastAPI reales contra el PostgreSQL en contenedor del runner, en modo `oidc` y sin `page.route`. Es el único trabajo del CI donde frontend, backend y base se hablan de verdad.

| Pieza | Ubicación |
| :--- | :--- |
| Configuración | `frontend/playwright.humo.config.ts` |
| Flujos | `frontend/tests/humo/` |
| Arrancador de la API | `tests/humo/servidor_humo.py` |
| Trabajo de CI | `humo` en `.github/workflows/zero-regression-pipeline.yml` |

Comandos locales, desde `frontend/`, con `TEST_DATABASE_URL` de una base de prueba ya migrada y `python` con `requirements.txt`:

```powershell
$env:BACKEND_URL = "http://127.0.0.1:5200"; $env:NEXT_PUBLIC_GOOGLE_CLIENT_ID = "humo-ci"; npm run build
```

```powershell
npx playwright test -c playwright.humo.config.ts
```

### Dónde corre y dónde no

| Evento | Humo | Arnés de Pytest | Base |
| :--- | :--- | :--- | :--- |
| Push a `dev/<persona>` | Compuerta | Completo | Contenedor |
| PR de `tarea/<persona>/...` hacia `dev/<persona>` | Compuerta | Por salas o completo, según el diff | Contenedor |
| PR de `dev/<persona>` hacia `main` | No corre | **Completo, obligatorio** | **Neon** |
| Push a `main` (la fusión) | No corre | **Completo, obligatorio** | **Neon** |

El humo es la compuerta de las ramas de los colaboradores, donde el trabajo cambia a diario y un fallo básico debe costar minutos, no la suite entera. Lo que llega a `main` ya pasó el humo en su rama: ahí no se repite y el arnés completo es obligatorio aunque el diff esté confinado a salas (el paso `Destino de la corrida` lo fuerza). Es el reparto clásico: humo en la compilación de cada día y regresión completa en la integración (McConnell, 1996; Humble y Farley, 2010).

Cuando el humo se omite, los arneses arrancan igual; cuando falla o se cancela, no arrancan.

En las ramas la base es un servicio `pgvector/pgvector:pg16` que nace vacío en cada corrida, sin secretos, y se migra con `alembic` antes de las pruebas; no hay turno de Neon ni comparación de revisión. Hacia `main` todo sigue contra Neon, y un PR hacia `main` no adopta la corrida del push de su rama (`corrida_cubierta.py`): esa corrida fue contra el contenedor, y el pooler y la latencia reales solo se comprueban ahí. Las ramas Neon de los colaboradores siguen vivas: las usan las pruebas físicas.

## 2. Flujos vigentes

| # | Flujo | Archivo |
| :--- | :--- | :--- |
| 1 | Identidad: token válido aceptado; ausente o falsificado, 401 | `01_identidad.spec.ts` |
| 2 | Aislamiento: otra organización responde 403 y no ve datos ajenos | `01_identidad.spec.ts`, `02_flujos.spec.ts` |
| 3 | RAT: crear una ficha en el formulario y que siga al recargar | `02_flujos.spec.ts` |
| 4 | Lectura de un módulo con datos del servidor (Hoja de Ruta) | `02_flujos.spec.ts` |
| 5 | Descarga real de la exportación del RAT: la huella mostrada es la de los bytes descargados | `03_descarga.spec.ts` |

Hay 5 flujos: el tope de la sección 4 ya está alcanzado.

## 3. Cuándo se añade un flujo

Se añade solo si se cumplen las tres condiciones:

1. **Si se rompe, un módulo entero deja de servir** a todo usuario, no a un caso particular.
2. **Cruza las tres capas:** interfaz, API y base.
3. **Ninguna prueba existente lo detectaría:** Pytest no ve el frontend y Playwright con `page.route` no ve el backend.

Un caso de borde, una regla de negocio o un permiso concreto van a Pytest o a Playwright, no aquí.

## 4. Límites

- **Máximo 5 flujos y 8 casos (`test(`).** Para añadir uno al tope, se retira otro.
- **Sin `page.route`** ni `AUTH_MODE=headers`.
- **Sin reintentos** (`retries: 0`). Un flujo intermitente se arregla o se retira: una compuerta que falla sola bloquea a todos.
- **Parada en el primer fallo** (`maxFailures: 1`).
- **Datos propios:** cada corrida crea dos organizaciones únicas y las borra al terminar. Nada depende de datos previos.

## 5. Orden: de rápido a lento

Lo barato va primero, para que el fallo cueste lo mínimo.

1. Revisión de Alembic, antes de compilar nada.
2. Compilación del frontend.
3. Casos sin navegador (`01_identidad.spec.ts`).
4. Casos con navegador, primero escritura y después lectura (`02_flujos.spec.ts`).
5. Descargas o recorridos largos (`03_descarga.spec.ts`).

Playwright corre los archivos en orden alfabético con un solo trabajador: el prefijo numérico fija el orden. Un archivo nuevo lleva el prefijo que le corresponde por tiempo medido.

## 6. Qué no cubre

- **El botón de Google.** La credencial se coloca donde la deja ese botón al volver; todo lo posterior es real.
- **Las claves reales de Google:** la clave pública se sustituye por una temporal. Firma, emisor, audiencia, vigencia, correo verificado, `users` y membresía sí se verifican.
- **Reglas de negocio, roles concretos y casos de borde:** son de Pytest.
- **El despliegue en Vercel:** el humo corre en el runner, no contra una URL publicada.
- **Conexión como `lopdp_app`:** usa el rol dueño de `TEST_DATABASE_URL`. En el contenedor ese rol es superusuario, así que `FORCE ROW LEVEL SECURITY` no se aplica a sus consultas: el aislamiento que ve el humo es el de la aplicación, y RLS y los permisos propios de `lopdp_app` son de `tests/test_rls_app_role.py`.
- **El pooler y la latencia de Neon:** el contenedor no los ejercita. Se comprueban en la corrida hacia `main`.

## 7. Autenticación

`tests/humo/servidor_humo.py` importa la aplicación y sustituye `security._clave_de_firma` por un RSA generado al arrancar. `app_core/security.py` no tiene ningún interruptor: la sustitución solo existe dentro de ese proceso.

El arrancador se detiene si detecta `VERCEL` o `VERCEL_*`, el host `ep-late-hall`, o si falta `HUMO_E2E=1`. Nada desplegado lo importa.

## 8. Si falla

1. Mire qué paso falló en el trabajo `Humo de extremo a extremo` y descargue `humo-report` (traza y captura).
2. `Migrar el contenedor a la cabeza de Alembic`: una migración de la rama está rota sobre una base vacía.
3. `Flujos de humo`: un flujo crítico está roto. Corríjalo antes de volver a lanzar: la suite completa no arrancará.
4. Si el fallo es de infraestructura (runner o imagen), se vuelve a lanzar la corrida. Playwright también queda detenido en ese caso: es el precio de la compuerta.

## 9. No espera turno de Neon

El humo no usa `esperar_turno_neon.py` ni toca Neon: cada corrida tiene su propio contenedor, así que no comparte cómputo con ningún arnés.

## 10. Revisión del coste

La compuerta suma tiempo a **todas** las corridas de las ramas de los colaboradores (las de `main` no la pagan) y solo ahorra en las que detiene. Compensa si:

```text
corridas detenidas por el humo × minutos ahorrados por corrida  >  corridas totales × minutos del humo
```

Se revisa con los datos de `gh run list` al añadir un flujo o cada mes. Si no compensa, el trabajo pasa a correr en paralelo, sin ser compuerta, o se retira.
