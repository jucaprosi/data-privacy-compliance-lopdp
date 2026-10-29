+++
id = "GOB-03"
titulo = "Kit y documentación de Biblioteca versionados"
ola = "D"
estado = "pendiente"
sala = "gobernanza, biblioteca"
depende_de = ["ORG-01", "ORG-08", "SEC-02", "BIB-105"]
propiedad = ["data/biblioteca/kit_v1/**", "governance/apoyo/BIBLIOTECA_DISENO.md", "governance/apoyo/BIBLIOTECA_FICHAS_OCHO_PLANTILLAS.md", "governance/apoyo/BIBLIOTECA_PLAN.md", "governance/apoyo/BIBLIOTECA_ESTADO.md", "governance/apoyo/BIBLIOTECA_README.md", "governance/artefactos/PRD.md", "governance/artefactos/TASKS.md", "governance/tareas/GOB-03.md", "governance/tareas/BIB-108.md", "governance/apoyo/BRIEFS_POR_BLOQUE.md"]
arbitro = "shasum -a 256 -c MANIFIESTO.sha256 desde data/biblioteca/kit_v1 (15 OK); python scripts/generar_indice_tareas.py --verificar; pytest tests/test_indice_tareas.py tests/test_vpa_map.py; python scripts/verificar_reparto.py --rama <rama> --bloque BL-84 --base origin/main"
rastros = ["¤adpa", "¤arbitro"]
+++

# GOB-03 · Kit y documentación de Biblioteca versionados

**Objetivo.** Dar un dueño único al kit original de Biblioteca y a sus documentos de gobernanza, fuera del PR de código de BIB-105.

## Entrega
- Incorporar `data/biblioteca/kit_v1/` (originales del commit 061fccb) sin alterar ningún original; sus huellas constan en `MANIFIESTO.sha256`.
- Incorporar `BIBLIOTECA_DISENO.md`, `BIBLIOTECA_FICHAS_OCHO_PLANTILLAS.md`, la línea del kit de `BIBLIOTECA_PLAN.md` y el Módulo 7 del PRD, sin modificar el apartado 7.1.
- Mantener `BIBLIOTECA_ESTADO.md` (estado y pendientes para otros chats, que enlaza y no sustituye a las fichas) y `BIBLIOTECA_README.md` (guía del módulo).
- Actualizar en BIB-108 la frase del kit «sin seguimiento Git» y añadir `GOB-03` a su `depende_de`.

## Criterios de aceptación
1. El manifiesto da 15 OK y cada hash coincide con el original recibido.
2. `README.md` del kit queda declarado como no original o añadido al manifiesto, según decida la propietaria.
3. El diff de la rama cabe en la `propiedad` (BL-84) y el índice de tareas verifica con código 0.
4. Ninguna de las ocho plantillas v0.1 se publica ni se importa a base de datos.
5. Las citas normativas de los documentos figuran como POR VERIFICAR mientras no exista revisión jurídica.

## No hagas
- No editar los originales del kit ni código de producción.
- No publicar ni importar las v0.1; no tocar `data/biblioteca/manifiesto_inicial.json` (BIB-108).
- No incluir credenciales, URLs de bases de datos ni datos reales de personas.
- No marcar hecha esta ni otra ficha.

## Dependencias
ORG-01 y ORG-08 (y, a través de ambas, ORG-00) poseyeron `PRD.md`; SEC-02 poseyó `BRIEFS_POR_BLOQUE.md`, y BIB-105 posee en el PR #158 `TASKS.md` y `BRIEFS_POR_BLOQUE.md`. Depender de ellas permite compartir esos archivos sin ejecución simultánea. BL-84 se registra en el PR de gobernanza de la tanda, tras fusionar el PR #158.

## Hecho cuando
Todos los criterios pasan con la salida de su árbitro; solo el coordinador cierra la ficha tras integrar su PR.
