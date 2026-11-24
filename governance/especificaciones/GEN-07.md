# GEN-07 · Firma electrónica, plantilla RAT y documentos de apoyo sin marca: el cliente de ANF en la configuración y los binarios fuera del repositorio
`¤sdd` `¤adpa` `¤arbitro`

## 1. Datos

Programa: GEN-01 §0. Hecho medido en `origin/main` ea6d26bf:
- `anf_stb_client.py:27`: `CLIENTE_ANF`, escrito en el código, es el identificador del cliente en el contrato con ANF AC y viaja en `testigos.cliente`. `tests/test_firma_anf_stb.py:79,100,105` fija ese valor y un `anf_api_id` de prueba con el nombre de la marca.
- `firma_electronica_service.py:69`: docstring con «EVYDENTIA / <marca>».
- `features/rat/domain/plantillas/salud.json:8-9`: `autoria` y `nota` nombran a la marca como autora y consultora (atribución con autorización).
- `FIRMA_ELECTRONICA_BOCETO.md` (3) e `INFORME_MODULO_FIRMA_ELECTRONICA.md` (7) nombran la marca y los binarios de `data/`.
- Binarios con la marca en el nombre o en el texto, que ningún código ni prueba lee: `Guia_Diseno_Plataforma_LOPDP_SMARTCIDI_2026_v1.1.docx.pdf`, `Guia_Modulo_Exposicion_Sancionatoria_LOPDP_SMARTCIDI_v1.1_FINAL (1).docx`, `Reporte_Assessment_LOPDP_PJL_17sep2026.pdf`, `data/Guia_Integracion_OneShot_SMARTCIDI.pdf`, `data/V1. Informe de entrega de STBS - SmartCidi.pdf`. El `.xlsx` de la escala no está aquí: lo renombra GEN-02.

## 2. API

Sin rutas. Configuración nueva: `ANF_CLIENTE` (`app_core/config.py`, `anf_cliente: str`, sin valor por defecto).

## 3. Reglas

- **R1 · Datos de un tercero, a la configuración.**
  - El identificador de cliente de ANF AC es un dato del contrato con un tercero: no se renombra, sale del código.
  - `anf_stb_client` lo lee de `config.anf_cliente`, y `configurado()` exige también ese valor. Sin él, la firma con ANF falla cerrada, como hoy sin credenciales.
  - Las pruebas usan valores de prueba neutros, por ejemplo `cliente-prueba` e `id-prueba`.
  - El propietario fija `ANF_CLIENTE` en cada entorno con su procedimiento de secretos (Antigravity) antes de desplegar esta ficha. Brief: `GEN-propietario-recuentos.md` §3.
- **R2 · Autoría de `salud.json`.** Es una atribución con autorización: el texto final de `autoria` y `nota` lo decide el propietario. **La ficha no se lanza sin ese texto anotado aquí.** Hasta entonces, esta sección queda pendiente.
- **R3 · Binarios fuera del repositorio.**
  - **Propuesta del Arquitecto:** los cinco binarios de §1 salen del repositorio con `git rm` y pasan a los documentos del propietario. Son documentos de terceros o del operador y ningún código los lee.
  - Los documentos que los citan los nombran por título, emisor y fecha, sin ruta. El propietario confirma o corrige la lista en el PR de gobernanza que anota su decisión, antes de lanzar.
  - El historial de git no se reescribe.
- **R4 · Documentos de apoyo.** `FIRMA_ELECTRONICA_BOCETO.md` e `INFORME_MODULO_FIRMA_ELECTRONICA.md` usan «Operador de la plataforma» y citan los documentos de R3 sin ruta.
- **R5 · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`GEN-07`).** Solo la propiedad. `app_core/config.py` solo gana el campo `anf_cliente`.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `ANF_CLIENTE` fijado con un valor de prueba, **entonces** la petición a ANF lleva ese valor en `testigos.cliente`; sin él, `configurado()` es falso y no se llama a ANF. Mutación m1: escribir el cliente en el código da rojo, porque la prueba fija otro valor. | `tests/test_firma_anf_stb.py` |
| **Dado** la plantilla de salud, **entonces** carga y valida con el texto del propietario. | `tests/test_rat_plantilla_salud.py` |

## 6. Trazabilidad

- Programa GEN-01 §0. Condiciones §5.4 del brief del CTO.
- Depende de las fichas hechas que comparten estos archivos: FIRMA-06, RAT-02 y MARCA-01.
