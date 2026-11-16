# Diseño: alta y revocación de capacidades editoriales de la Biblioteca (solo ramas de prueba)

Arquitecto de soluciones ADPA · 2026-11-08 · Base: `origin/main` 5499287. Solo diseño.

## 1. Hechos del código que deciden la forma

1. `alembic/versions/20261025_biblioteca_base.py`:
   - `lopdp_app` solo tiene **SELECT** sobre `biblioteca_capacidades` y `biblioteca_auditoria_capacidades`;
   - la migración dice: «Las capacidades solo las cambia el propietario»;
   - las dos tablas tienen **RLS forzada**, con una sola política, `bib_cap_propia` (SELECT);
   - el disparador `bib_auditar_capacidad` (SECURITY DEFINER) ya escribe `alta`, `revocacion`, `reactivacion`, `modificacion` y `baja`, con `actor_id` y `rol_bd = session_user`;
   - los CHECK ya exigen `motivo` no vacío al conceder, y `revocada_por` más `motivo_revocacion` al revocar.
2. **No hay ningún CHECK que impida la autoconcesión** (`usuario_id = concedida_por`), ni la autorrevocación.
3. `features/biblioteca/services/autorizacion.py:15` solo lee las capacidades vigentes (`revocada_en IS NULL` y usuario activo).
4. PRD §Biblioteca C (línea 332): ser administrador de la organización o de la plataforma no concede capacidades; sin asignaciones humanas explícitas se deniega todo.
5. `scripts/cargar_plantillas_pmv.py` es el patrón de guardia: variable de URL propia, `--confirmar-rama-desarrollo`, y lista de hosts prohibidos (producción y la rama test compartida), comprobada sin abrir conexión.

## 2. Decisiones

**Sala y compuerta:** `features/biblioteca`, detrás de `biblioteca_service.py`. La lógica va en un motor nuevo de la sala. El script de `scripts/` solo usa la compuerta, igual que BIB-109.

**Forma mínima: un script de desarrollo, sin endpoint.**
- Un endpoint tendría que escribir como `lopdp_app`, y eso exige darle INSERT y UPDATE sobre `biblioteca_capacidades`. Sería abrir una vía de escalada de privilegios que la migración cerró a propósito, y cualquier fallo de autorización en la API acabaría concediendo capacidades.
- El script escribe con la credencial del **dueño de la base de la rama de prueba**, que solo tienen las personas (Juan Carlos, Aleczandra y José).
- Un endpoint con pantalla de plataforma queda para una ficha posterior, con su propia función SECURITY DEFINER y su revisión de Seguridad. Fuera de alcance.

**Quién concede:** la persona que tiene la credencial de dueño de la rama de prueba. En la fila, `concedida_por` / `revocada_por` es el `users.id` de esa persona (`--otorgante`), que debe existir, estar activa y **no** ser el destinatario. Ni `admin_organizacion` ni `operador_plataforma` dan capacidades por sí mismos: el script no consulta roles empresariales.

## 3. Reglas, cada una con su árbitro

| Regla | Dónde se hace cumplir | Prueba |
|---|---|---|
| Nadie se concede a sí mismo | En la base: `CHECK (usuario_id <> concedida_por)` y `CHECK (revocada_por IS NULL OR revocada_por <> usuario_id)` (migración nueva), y antes en el motor con el error `BIB_AUTOCONCESION` | Conceder con `--otorgante` igual al destinatario: rechazo en el motor; con el motor saltado por SQL directo, rechazo de la base |
| Motivo obligatorio para conceder, revocar y reactivar | CHECK existentes, más validación en el motor (`BIB_MOTIVO_OBLIGATORIO`) | Motivo vacío o de espacios: rechazo |
| Auditoría con alta, revocación y reactivación | Disparador existente; el motor nunca borra (revoca con UPDATE) | Tras conceder, revocar y reactivar quedan 3 filas en `biblioteca_auditoria_capacidades` con actor, motivo y `rol_bd` |
| Nunca borrar | El motor no ofrece la baja, y la migración no da DELETE | No hay función ni opción de baja; la prueba busca `DELETE` en el motor y falla si aparece |
| Nunca contra producción ni contra la rama test compartida | Guardia en el script, antes de importar la sesión: `BIB_CAPACIDADES_DATABASE_URL` obligatoria, `--confirmar-rama-desarrollo`, rechazo si `apunta_a_produccion(url)` (`app_core/huellas_produccion.py`) o si el host está en la lista de BIB-109. El script no imprime la URL | Con la huella de producción o la de la rama test: código 2 y ninguna conexión (se comprueba con una sesión simulada que falla si se llama) |
| Solo las cuatro capacidades | El CHECK existente y el `enum Capacidad` | Una capacidad inventada: rechazo |
| El dueño puede escribir pese a la RLS forzada | Migración: políticas `bib_cap_propietario_alta` (INSERT) y `bib_cap_propietario_cambio` (UPDATE) **`TO CURRENT_USER`** (el rol que migra, es decir, el dueño), con `WITH CHECK (usuario_id <> concedida_por)`. Sin políticas para `lopdp_app`, y sin DELETE | La prueba conecta como el dueño y concede; conectada como `lopdp_app`, el INSERT se rechaza |

Sobre la última fila: con `FORCE ROW LEVEL SECURITY`, el dueño de la tabla también queda sujeto a las políticas, salvo que su rol tenga BYPASSRLS. Hoy solo hay una política de SELECT, así que la escritura del dueño depende del atributo del rol, que en el proveedor del PMV y en Cloud SQL no es el mismo. La política explícita lo vuelve determinista. **Seguridad lo revisa**, porque cambia la superficie de escritura de una tabla de permisos.

Uso previsto (lo ejecuta una persona, en la rama de prueba):
```
python scripts/capacidades_biblioteca.py --listar
python scripts/capacidades_biblioteca.py --conceder --usuario U --capacidad editor --otorgante O --motivo "…" --confirmar-rama-desarrollo
python scripts/capacidades_biblioteca.py --revocar  --usuario U --capacidad editor --otorgante O --motivo "…" --confirmar-rama-desarrollo
```
Conceder una capacidad revocada la **reactiva** (UPDATE: limpia la revocación y escribe un nuevo `concedida_por` y un nuevo `motivo`); el disparador la registra como `reactivacion`. Para la guía de las 12 plantillas basta con cuatro personas de prueba distintas, una por capacidad, porque nadie revisa ni publica su propia versión.

## 4. Ficha propuesta

```
+++
id = "BIB-117"          # el número lo asigna Tech Lead
titulo = "Alta, revocación y reactivación de capacidades editoriales por script, solo en ramas de prueba"
ola = "indep"
estado = "pendiente"
sala = "biblioteca"
depende_de = ["BIB-109"]
propiedad = [
  "features/biblioteca/services/capacidades_admin.py",
  "features/biblioteca/biblioteca_service.py#BIB-117",
  "features/biblioteca/domain/errores.py#BIB-117",
  "scripts/capacidades_biblioteca.py",
  "alembic/versions/20261108_biblioteca_capacidades_propietario.py",
  "tests/test_bib117_capacidades.py",
]
crea = [
  "features/biblioteca/services/capacidades_admin.py",
  "scripts/capacidades_biblioteca.py",
  "alembic/versions/20261108_biblioteca_capacidades_propietario.py",
  "tests/test_bib117_capacidades.py",
]
arbitro = "pytest tests/test_bib117_capacidades.py + python scripts/generar_indice_tareas.py --verificar"
+++
```

**Precondición R-PROP-EXISTE:** las marcas `=== BIB-117 ===` / `=== fin BIB-117 ===` **no existen** en `biblioteca_service.py` ni en `domain/errores.py`, y ninguna ancestro las siembra. Tech Lead las **siembra vacías en el mismo PR de gobernanza** que crea la ficha. Así existen en HEAD cuando arranca el sub chat (regla 1a), y la ficha no añade secciones por su cuenta.

**Dependencias:**
- BIB-109: patrón de guardia y lista de hosts. La ficha la reutiliza **leyéndola**; si conviene compartir la lista, se expone por la compuerta, sin copiarla.
- `app_core/huellas_produccion.py`: solo lectura.
- La migración base de Biblioteca: ya está en main.
- La migración nueva aplica `FUSION_ALEMBIC` antes de fusionar (regla de reparto sin rama al día).

**Entrega:**
- motor `capacidades_admin.py` con `conceder`, `revocar` y `listar`; sin borrado;
- exportación por la sección BIB-117 de la compuerta;
- códigos `BIB_AUTOCONCESION`, `BIB_MOTIVO_OBLIGATORIO`, `BIB_CAPACIDAD_INVALIDA` y `BIB_USUARIO_INACTIVO` en su sección de errores;
- script con la guardia;
- migración con los dos CHECK y las dos políticas del dueño;
- en la guía de `BIBLIOTECA_ESTADO.md` §11, el paso 2 lo escribe quien ya redacta esa guía (no es propiedad de esta ficha), citando el comando.

**Pruebas (PostgreSQL real de la CI, con el dueño y con `lopdp_app`):**
1. Conceder, revocar y reactivar: estado vigente correcto, 3 filas de auditoría con actor y motivo, y `autorizar()` permite y deniega en cada paso.
2. Autoconcesión: la rechaza el motor y, por SQL directo, también la base.
3. Motivo vacío y capacidad inventada: rechazo.
4. `lopdp_app` no puede insertar ni actualizar capacidades, ni siquiera tras la migración.
5. Guardia: con la huella de producción, con el host de la rama test y sin `--confirmar-rama-desarrollo`, código 2 y ninguna conexión abierta.
6. No existe ninguna ruta de borrado: ni opción `--baja` ni `DELETE` en el motor.

**Mutaciones que deben fallar:**
- M1: quitar el CHECK `usuario_id <> concedida_por` de la migración: la prueba 2 por SQL directo falla.
- M2: la guardia no llama a `apunta_a_produccion`: la prueba 5 falla.
- M3: revocar con DELETE en vez de UPDATE: falla la prueba 1, porque la auditoría registra `baja` y no `revocacion`, y falla la 6.

**Revisión de Seguridad antes del reparto:** sí, porque toca permisos (políticas y CHECK de una tabla de capacidades).
