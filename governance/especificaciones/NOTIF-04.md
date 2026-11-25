# NOTIF-04 · Aviso de concesiones y retiros de capacidades editoriales
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Usa `avisos_plataforma` de NOTIF-02, con el tipo nuevo `capacidad_editorial` y `referencia` = el `id` del cambio. Lee `cambios_de_capacidades(desde)` por el pasillo de la biblioteca (BIB-411) y `listar_operadores_activos()` por el de plataforma (OPE-01). Base `origin/main` f78f8b92.

## 2. API

`POST /avisos/sincronizar-capacidades` (`api/routers/avisos_capacidades.py`), para un operador, como `POST /avisos/sincronizar` de NOTIF-02. Lo llama la misma ejecución programada, que el propietario amplía por el brief. Los avisos se ven en Inicio › Avisos.

## 3. Reglas

- **R1 · Destinatarios.** Cada cambio crea un aviso para cada operador activo, incluidos quien lo hizo y quien lo recibió, sin duplicar (UNIQUE de NOTIF-02).
- **R2 · Texto** (UX/UI, 2026-11-25). Título «Capacidad editorial concedida» o «Capacidad editorial retirada». Texto:
  - para quien la recibe o la pierde: «{por} te concedió la capacidad {X}.» o «{por} te retiró la capacidad {X}.»;
  - para los demás: «{por} concedió a {a quién} la capacidad {X}.» o «{por} retiró a {a quién} la capacidad {X}.»;
  - {X} es Editor, Revisor técnico o Publicador. Después, «Motivo: «{motivo}».», con el motivo cortado a 200 caracteres, con «…» si se corta, y en texto plano; sin motivo no hay hueco.
  - Enlace «Ver capacidades editoriales», a `/plataforma/capacidades`. Sin recordatorios.
- **R3 · Palabras.** Las de NOTIF-02 R5.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`NOTIF-04`).** Solo los archivos de la propiedad. Otras salas, solo por sus pasillos.

## 4. Interfaz

La bandeja de NOTIF-02, sin cambios.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** tres operadores activos y una concesión, **entonces** `sincronizar-capacidades` crea tres avisos, y al repetirlo no crea más. Mutación m1: avisar solo a quien la recibe da rojo. | `tests/test_notif04_avisos_capacidades.py` |
| **Dado** un retiro, **entonces** el aviso dice «retiró a» y el motivo a los demás, y «te retiró» a quien la pierde. Mutación m2: no incluir el motivo da rojo. | ídem |
| **Dado** un aviso de este tipo, **entonces** no tiene recordatorios ni contiene «undefined», «null», «None», «{», «}», «, ,» ni dos espacios seguidos. Mutación m3: programarle un recordatorio da rojo. | ídem |
| **Dado** la sala, **entonces** solo importa otras salas por sus pasillos. | `tests/test_adpa_bulkhead.py` |

## 6. Trazabilidad

- **PRD:** notificaciones de la plataforma y Módulo 7.
- Decisión C del CTO (2026-11-25), brief del CTO `ARQUITECTO_UXUI_BIBLIOTECA_OPERADORES` (2026-11-25) y parte de pantalla del UX/UI `UXUI_PARTE_PANTALLA_BIBLIOTECA_OPERADORES` (2026-11-25), base `origin/main` f78f8b92.
