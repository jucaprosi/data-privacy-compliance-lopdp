# Tanda de 20 fichas libres · propuesta del Arquitecto ADPA

Fecha: 2026-11-13. Para el Tech Lead, a pedido del CTO. Medido en `origin/main` 70329532: estado y `depende_de` de cada ficha, propiedad con comodines, migraciones y si tiene especificación. En `main` hay 291 fichas hechas, 35 en curso y 41 pendientes.

## Resumen

- **Solo cinco fichas pendientes están libres hoy** (sin ninguna dependencia abierta): RM-26, SEC-24, INC-03f, DEMO-03f y FIRMA-02. Con RET-00, que aún no tiene ficha, son seis.
- Las otras catorce de la lista dependen solo de fichas de esta misma tanda o de fichas que hoy están `en_curso`. No necesitan al propietario, pero no pueden empezar hasta que su dependencia se fusione. Cada una dice de cuál.
- **Cuatro llevan migración**, el máximo pedido. Orden de entrada: FIRMA-02 → FOR-01 → RM-25b → RM-27.
- **Dieciocho no tienen especificación en `main`.** Las seis de RET están escritas en la rama `tarea/juan-carlos/espec-ret` (35b1663d). Las otras doce las debo yo.

## Lista

| # | Ficha | Dominio | Depende de | Migración | Frontend | Especificación | Modelo |
| :-- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | RET-00 | pruebas | — | no | no | en `espec-ret` | sonnet |
| 2 | RM-26 | roadmap | — | no | no | **falta** | sonnet |
| 3 | SEC-24 | seguridad | — | no | no | **falta** | sonnet |
| 4 | INC-03f | incidentes | — | no | sí (UX/UI) | **falta** | sonnet |
| 5 | DEMO-03f | demo | — | no | no | **falta** | sonnet |
| 6 | FIRMA-02 | firma | — | **1.ª** | sí (UX/UI) | sí | sonnet |
| 7 | RET-01 | seguridad | RET-00 | no | no | en `espec-ret` | opus |
| 8 | RET-05 | nube y frontend | RET-01, SEC-21 (en curso) | no | sí | en `espec-ret` | sonnet |
| 9 | RET-02 | roadmap y evidencias | RET-01, EVI-04 (en curso) | no | sí | en `espec-ret` | opus |
| 10 | RET-03 | roadmap | RET-02 | no | sí | en `espec-ret` | sonnet |
| 11 | IA-06 | inferencia y roadmap | RM-26, RET-03 | no | no | **falta** | sonnet |
| 12 | RM-27 | roadmap | IA-06 | **4.ª** | no | **falta** | sonnet |
| 13 | FOR-01 | derechos y cumplimiento | EVI-04 (en curso) | **2.ª** | sí (UX/UI) | sí | sonnet |
| 14 | RM-25b | roadmap | ORG-22 (en curso), RET-02 | **3.ª** | no | **falta** | sonnet |
| 15 | IA-09 | inferencia | IA-04 (en curso) | no | sí (UX/UI) | **falta** | sonnet |
| 16 | SEC-25 | seguridad | GCP-06 (en curso) | no | no | **falta** | sonnet |
| 17 | SEC-23b | seguridad | SEC-23 e IA-07 (en curso) | no | no | **falta** | sonnet |
| 18 | NORM-02b | normativa | NORM-02 (en curso) | no | no | **falta** | opus |
| 19 | DIAG-15 | diagnóstico | DIAG-07 (en curso) | no | sí (UX/UI) | **falta** | sonnet |
| 20 | RET-06 | pruebas, por dominio | RET-00, RET-01 | no | no | en `espec-ret` | sonnet |

Sin especificación en `main` hay dieciocho. Seis son de RET y ya están escritas en su rama. Las otras doce están por escribir: RM-26, SEC-24, INC-03f, DEMO-03f, IA-06, RM-27, RM-25b, IA-09, SEC-25, SEC-23b, NORM-02b y DIAG-15.

## Por qué opus en NORM-02b

Lista las organizaciones activas con su administrador y su delegado: es una lectura entre organizaciones, fuera del aislamiento por organización. Un error ahí filtra datos de una organización a otra. Las demás siguen la regla (RET-01 y RET-02 en opus, el resto en sonnet).

## Cadenas dentro de la tanda

- **Retiro:** RET-00 → RET-01 → RET-02 → RET-03 → IA-06 → RM-27. RET-05 y RET-06 salen de RET-01.
- **Roadmap comparte archivos:** RET-02, RET-03 y RM-25b tocan `api/routers/roadmaps.py`; RET-03 e IA-06 tocan `generacion_engine.py`. Por eso van en fila y no en paralelo.
- **RET-06 entra solo con los dominios sin ficha en curso.** El dominio diagnóstico espera a DIAG-07.

## Lo que queda fuera y por qué

- **RET-07 e IA-08:** son las últimas del programa. IA-08 espera a IA-04, IA-05, IA-06 e IA-07; RET-07 espera a todas.
- **API-02, CCTV-01, CON-01, DER-01, RAT-08, TER-02, CAPA-04:** llevan migración y ya hay cuatro. API-02 y CCTV-01 esperan además a BOV-01; CON-01 y RAT-08, a RAT-07; TER-02, a TER-01; CAPA-04, a cuatro fichas en curso.
- **BOV-02, BOV-03, BOV-04, CCTV-02, GOCA-01, GOVW-01, NORM-03:** dependen de fichas que aún no están en curso.
- **DEMO-05b, c y d, DEMO-07, GCP-05b:** dependen de DEMO-05 o de EP-09, que esperan al propietario.
- **MARCA-04, ORG-23, PLAT-01, CI-26:** libres en cuanto cierren DIAG-07, ORG-22 u ORG-20. Son las primeras suplentes si alguna de las veinte se cae.

## Antes de escribir las fichas

1. **FIRMA-02 tiene dos comodines en su propiedad** y hay que concretarlos. Además figura como dueña de una lista de pendientes del árbitro vigente de menciones: su PR la tiene que vaciar.
2. **FOR-01:** la lista concreta de 29 archivos ya está enviada; depende de EVI-04.
3. **NORM-02b:** falta fijar el pasillo. Propuesta: sección propia en `app_core/pasillo/plataforma.py`, con una función que devuelve solo identificador de organización, correo del administrador y correo del delegado de las organizaciones activas, y nada más. Lo cierro en su especificación.
4. **SEC-24 y RET-01 tocan la misma dependencia de la cabecera de organización** (`api/dependencies.py` y `app_core/security.py`). Hay que ordenarlas; propongo SEC-24 antes de RET-01.
5. **Ninguna especificación ni ficha de esta tanda nombra a los proveedores retirados.** El árbitro vigente no admite menciones nuevas y se pone en rojo.

## Lo que no medí

- Los dueños actuales de cada archivo de las doce fichas con especificación por escribir: lo mido al escribir cada una.
- Si las fichas `en_curso` de las que dependen catorce de la lista están cerca de fusionarse.
