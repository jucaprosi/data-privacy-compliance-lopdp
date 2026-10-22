+++
id = "DEV-01"
titulo = "Modo desarrollador para pruebas en físico: organización de demostración con un usuario por rol en una rama de desarrollo"
ola = "D"
estado = "hecha"
sala = "operaciones"
depende_de = ["ORG-02", "ORG-06", "ORG-07", "SEC-07"]
propiedad = ["scripts/crear_organizacion_dev.py", "tests/test_crear_organizacion_dev.py", "governance/operaciones/PRUEBAS_EN_FISICO.md"]
arbitro = "pytest tests/test_crear_organizacion_dev.py + suite completa contra una rama Neon de desarrollo; el propietario sigue la guía y entra con cada rol en el navegador"
rastros = ["¤arbitro", "¤rbac-tenant"]
+++

# DEV-01 · Modo desarrollador para pruebas en físico

**Objetivo.** Hoy no hay forma de probar la plataforma a mano, rol por rol. Ningún código crea una organización ni su primer administrador (en modo `oidc`, sin rol activo, la API responde 403), y `scripts/seed_database.py` solo carga solicitudes ARCO de ejemplo en un tenant fijo. El modo `headers` ya existe para desarrollo (el frontend envía `X-Tenant-ID`, y para la hoja de ruta `X-User-ID` y `X-Role`; ver `frontend/src/lib/auth/cabeceras.ts`), pero falta lo que se prueba con él: una organización con datos coherentes y **un usuario por cada rol**. Esta tarea da al propietario y a los agentes un entorno de pruebas en físico reproducible, sin tocar nunca producción.

## Entrega
- `scripts/crear_organizacion_dev.py` (ejecutable con el intérprete del proyecto), que en la base indicada por `TEST_DATABASE_URL` crea, de forma **idempotente** (ejecutarlo dos veces no duplica nada):
  - una organización de demostración con tamaño configurado;
  - un usuario por rol: `admin_organizacion`, `coordinador`, `implementador`, `responsable_area` y `dpo`, **respetando las reglas vigentes** (el `dpo` sin ningún otro rol, ORG-01; ninguna combinación que exija una excepción de ORG-02);
  - una estructura orgánica mínima (alta dirección y dos unidades, con jefatura y una vacante; ORG-07) y la designación formal del delegado (ORG-06);
  - y al terminar imprime los identificadores que hay que poner en `frontend/.env.local` y en las cabeceras del modo `headers` para entrar como cada rol.
- **Fallo cerrado contra producción:** el script se niega a ejecutarse si el host de la URL es el de producción (`ep-late-hall-b50bpbk5`) o si `AUTH_MODE` no es `headers`; imprime el host (sin contraseña) antes de escribir nada.
- `governance/operaciones/PRUEBAS_EN_FISICO.md`: guía paso a paso para el propietario (PowerShell, completa y pegable): crear la organización de demostración en su rama Neon de desarrollo, arrancar backend y frontend en modo `headers`, cambiar de rol y qué comprobar con cada uno (qué ve y qué no ve). Señala lo que **no** se puede probar así (el inicio de sesión real con Google: ver OPS-05).
- `tests/test_crear_organizacion_dev.py`, con base real: crea lo prometido; es idempotente; los roles cumplen las incompatibilidades del DPO y de la separación de funciones; se niega con el host de producción (prueba sin conexión real, con una URL ficticia de ese host). Sin SQL interpolado.
- **Prueba de mutación documentada:** quitar a propósito la comprobación del host de producción y comprobar que su prueba falla.

## Límites
- No crea endpoints ni pantallas, y no es el alta real de organizaciones: eso es ORG-09.
- No toca producción ni la rama `test` compartida.
- No guarda credenciales ni identificadores reales de personas: los usuarios de demostración usan correos de un dominio reservado para pruebas (`example.test`).

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
