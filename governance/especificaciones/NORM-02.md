# NORM-02 · Centro de Vigilancia Normativa
`¤sdd` `¤inteligencia-normativa` `¤vigilancia-spdp` `¤navegacion-menus`

## 1. Datos

Usa las tablas de NORM-01. Añade la traza de revisión en `normativa_resoluciones` (`revisada_por`, `revisada_en`, ya declaradas) y una nota de revisión obligatoria al pasar a `vigente`, `observada`, `reformada` o `derogada`.

## 2. API

- `GET /api/v1/normativa/resoluciones?numero=&anio=&q=&organo=&materia=&estado=` -> `200 OK`, paginado.
- `GET /api/v1/normativa/resoluciones/{id}` -> `200 OK` con sus versiones.
- `GET /api/v1/normativa/resoluciones/{id}/original` -> `200 OK` con URL firmada de 5 minutos.
- `POST /api/v1/normativa/monitoreo` -> `202 Accepted` (operador, DPO o administrador).
- `GET /api/v1/normativa/monitoreo` -> `200 OK`, bitácora de corridas.
- `POST /api/v1/normativa/resoluciones/{id}/revision` con `{"estado", "nota"}` -> `200 OK`; `403` sin rol; `422 NORMATIVA_NOTA_OBLIGATORIA` sin nota.

## 3. Reglas

- **R1 · Validación humana (`INV_NORMATIVA_HUMAN_LEGAL_VALIDATION`).** Solo el DPO o el administrador cambian el estado; cada cambio guarda quién, cuándo y la nota.
- **R2 · Operador sin juicio jurídico.** El operador de plataforma dispara corridas y ve la bitácora, pero no homologa (403).
- **R3 · Descarga controlada.** El original se entrega solo por URL firmada de corta vida; nunca por una ruta pública.
- **R4 · Avisos.** Una corrida con resoluciones nuevas o versiones nuevas avisa al administrador y al DPO de cada organización activa; una corrida `fallida` avisa al operador.
- **R5 · Sin tokens internos.** La pantalla no muestra rastros ni códigos de gobernanza (`¤interfaz`).

## 4. Interfaz

Pantalla «Vigilancia normativa» en el menú Conocimiento:
- catálogo en tabla densa con filtros y estado en etiqueta de color;
- panel lateral con el visor PDF y el historial de versiones;
- pestaña «Bitácora» con las corridas;
- botón «Revisar ahora» según el rol.

Legible en tema claro y oscuro con variables de superficie (`FE-18`).

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** tres resoluciones de años distintos, **cuando** se filtra por `anio=2026`, **entonces** solo vuelven las de 2026. | `test_filtro_por_anio` |
| **Dado** una URL de descarga emitida, **cuando** pasan más de 5 minutos, **entonces** deja de servir el archivo. | `test_url_original_caduca` |
| **Dado** el DPO marca una resolución como `vigente` con nota, **cuando** se consulta, **entonces** muestra el estado con quién y cuándo. | `test_revision_por_dpo_con_traza` |
| **Dado** el operador de plataforma, **cuando** intenta homologar, **entonces** recibe 403. | `test_operador_no_homologa` |
| **Dado** una corrida que encuentra una resolución nueva, **cuando** termina, **entonces** se emite un aviso al administrador y al DPO de cada organización activa. | `test_aviso_por_organizacion` |
| **Dado** el catálogo en el navegador, **cuando** se abre una resolución, **entonces** el visor carga el PDF y no hay datos simulados. | `frontend/tests/normativa/centro.spec.ts` |

## 6. Trazabilidad

- `PRD.md` Módulo 6.2 y menú 9; invariante 41 de `INVARIANTS.md`.
