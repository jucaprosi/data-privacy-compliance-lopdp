+++
id = "SEC-11"
titulo = "Comprobar desde fuera que producción exige el acceso con Google (AUTH_MODE)"
ola = "D"
estado = "hecha"
sala = "gobernanza"
depende_de = ["SEC-03", "OPS-03", "ORG-09"]
propiedad = ["scripts/verificar_despliegue.py", "tests/test_verificar_despliegue.py"]
arbitro = "pytest tests/test_verificar_despliegue.py + el propietario ejecuta el verificador contra producción con código 0"
rastros = ["¤seguridad", "¤arbitro"]
+++

# SEC-11 · Producción exige el acceso con Google

**Objetivo.** Nadie ha comprobado con qué `AUTH_MODE` corre el backend desplegado. Si fuera `headers`, cualquiera podría declararse cualquier usuario, rol u operador de la plataforma con una cabecera. La comprobación debe hacerse desde fuera, sin credenciales del despliegue.

## Fundamento
`app_core/security.py`: en `oidc` toda petición sin `Authorization: Bearer` recibe **401** antes de mirar el rol; en `headers` se aceptan `X-User-ID`/`X-User-Email` y se pasa al control de rol (**403** si no hay membresía u operador). Una petición con cabeceras inventadas distingue los dos modos sin crear nada.

## Entrega
- `scripts/verificar_despliegue.py` gana una comprobación `modo_autenticacion`: envía a `GET /api/v1/plataforma/organizaciones` (y a un endpoint de organización con `X-Tenant-ID`, `X-User-ID` y `X-Role` inventados) y exige **401**. Un 403, un 200 o cualquier otro código hace fallar el verificador con un mensaje que diga «el despliegue acepta identidad por cabeceras». Solo peticiones `GET`, sin cuerpo, sin datos reales.
- Una opción `--esperar-modo {oidc,headers}` (por defecto `oidc`) para poder usarlo también contra un despliegue de desarrollo.
- `tests/test_verificar_despliegue.py`: casos con respuestas simuladas (401 → pasa; 403, 200 y 500 → falla; error de red → falla con motivo).
- **Prueba de mutación documentada:** invertir la condición (aceptar 403) y comprobar que una prueba falla.

## Para el propietario (tras fusionar)
Ejecutar `python scripts/verificar_despliegue.py <url-de-producción>` y pegar la salida. Si falla, el arreglo es fijar `AUTH_MODE=oidc` en Vercel y volver a desplegar.

## Límites
- No cambia la configuración de Vercel ni el código de autenticación.
- No usa tokens reales ni crea datos.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
