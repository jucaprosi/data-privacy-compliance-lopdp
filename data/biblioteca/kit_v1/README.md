# Kit de implementación de Biblioteca EVYDENTIA

Este directorio conserva en Git los 15 archivos útiles recibidos en el kit de diseño del 24 de octubre de 2026. Se excluyen `.DS_Store` y el archivo temporal de Word `~$D_Biblioteca_EVYDENTIA_Tres_Entregas.docx` porque no son fuentes del producto.

La incorporación preserva los archivos originales y sus hashes. No publica plantillas, no importa registros en base de datos y no convierte el estado editorial de los ocho maestros v0.1: todos permanecen en revisión.

## Integración en el repositorio

| Fuente del kit | Integración canónica |
| :--- | :--- |
| PRD de tres entregas | Consolidado en `governance/artefactos/PRD.md`, Módulo 7 |
| Diseño funcional | Original DOCX aquí y versión revisable en `governance/apoyo/BIBLIOTECA_DISENO.md` |
| Fichas de ocho plantillas | Original DOCX aquí y versión revisable en `governance/apoyo/BIBLIOTECA_FICHAS_OCHO_PLANTILLAS.md` |
| Backlog y esquemas JSON | Conservado en `especificacion/backlog_y_esquemas.json`; las 23 fichas canónicas viven en `governance/tareas/BIB-*.md` |
| Especificación JSON | Conservada en `especificacion/especificacion_biblioteca.json` como contrato de diseño |
| Catálogo maestro XLSX | Conservado en `catalogo/catalogo_maestro.xlsx` como fuente editorial |
| Ocho plantillas | Conservadas en `plantillas/v0.1/` como referencias no publicadas |
| Guía de lectura | Conservada como `LEER_PRIMERO.txt` |

## Reglas de uso

- No editar los originales para adaptar la implementación. Las correcciones se realizan mediante una nueva versión identificada.
- Verificar `MANIFIESTO.sha256` antes de importar o revisar contenido.
- No ofrecer como descarga un archivo que no esté publicado por el flujo editorial.
- No usar ejemplos ficticios como datos de una organización.
- La futura importación reproducible e idempotente corresponde a BIB-108 y requiere autorización y una base de desarrollo aislada.
