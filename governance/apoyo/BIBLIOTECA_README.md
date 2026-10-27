# Biblioteca documental EVYDENTIA

> **Borrador** sin revisión de la propietaria; propiedad propuesta: GOB-03. Guía para quien use o herede el módulo. El estado vivo está en `governance/apoyo/BIBLIOTECA_ESTADO.md`; el estado de cada tarea, solo en la cabecera de `governance/tareas/BIB-*.md`.

## Qué es

Sala ADPA `biblioteca` de la Plataforma LOPDP 360. Administra plantillas maestras de protección de datos (Word y Excel) con revisión técnica y jurídica independiente, y, en entregas futuras, los documentos de cada organización generados a partir de ellas. Una plantilla publicada no certifica cumplimiento ni sustituye la revisión jurídica de cada caso.

## Dónde está cada cosa

| Qué | Ruta |
| :--- | :--- |
| Compuerta de la sala (único punto de entrada desde otras salas) | `features/biblioteca/biblioteca_service.py` |
| Reglas editoriales puras y validación de archivos | `features/biblioteca/domain/editorial.py` |
| Contratos de documentos de empresa (aún sin implementar) | `features/biblioteca/domain/base.py` |
| Persistencia y transiciones | `features/biblioteca/services/editorial.py` |
| Capacidades editoriales | `features/biblioteca/services/autorizacion.py` |
| API | `api/routers/biblioteca_editorial.py` (`/biblioteca/editorial`) |
| Migración | `alembic/versions/*_biblioteca_base.py` |
| Cliente y vista editorial | `frontend/src/lib/biblioteca/`, `frontend/src/components/biblioteca/editorial/` |
| Kit original (maestros v0.1, catálogo, especificación) | `data/biblioteca/kit_v1/` (llega con GOB-03) |
| Plan, diseño y fichas de las ocho plantillas | `governance/apoyo/BIBLIOTECA_*.md` |
| Requisitos y criterios de aceptación | `governance/tareas/BIB-101.md` … `BIB-307.md` |

## Cómo funciona la publicación de un maestro

1. Un **editor** crea la versión (`codigo`, `version`, `formato`) y carga ficha y archivo. Cada cambio sube la `generacion`.
2. Un **revisor técnico** y un **revisor jurídico**, que no sean autores, dictaminan sobre la generación vigente.
3. Un **publicador**, que tampoco sea autor, publica. Si ya hay una publicada del mismo código, la nueva debe declarar `sustituye_id` y la anterior pasa a `sustituida`.
4. Publicada, retirada o sustituida, la versión es inmutable; los cambios van en una versión nueva.

Las capacidades se asignan en `biblioteca_capacidades`. Ser administrador de una organización o de la plataforma no las concede.

## Reglas para trabajar en el módulo

- Lee la ficha de tu tarea y escribe solo los archivos de su `propiedad`. Comprueba con `python scripts/verificar_reparto.py --rama <rama> --bloque <BL-xx> --base origin/main`.
- Otras salas se usan solo por su compuerta `<sala>_service.py`; cada tarea edita solo su sección `#BIB-xxx` de la compuerta.
- No edites los originales del kit. Su integridad se comprueba con `shasum -a 256 -c MANIFIESTO.sha256` desde `data/biblioteca/kit_v1/`.
- Las ocho plantillas v0.1 no se publican sin la aprobación expresa de la propietaria, una por una.
- No cites artículos de la LOPDP ni de su Reglamento de memoria; las referencias de las plantillas están POR VERIFICAR hasta su revisión jurídica.
- No guardes credenciales, URLs de bases de datos ni datos reales de personas, tampoco en ejemplos o pruebas.
- Las pruebas con base de datos usan una rama propia de Neon (`TEST_DATABASE_URL`); sin ella, el resultado se informa como no verificado.

## Cómo comprobar

```bash
pytest tests/test_bib_105_editorial.py
```

```bash
python scripts/generar_indice_tareas.py --verificar
```

## Fuera de alcance comprometido

Importación inteligente de documentos externos, edición colaborativa de Word, firma electrónica, certificación automática de cumplimiento y los 40 documentos planificados del catálogo (PRD Módulo 7 F).
