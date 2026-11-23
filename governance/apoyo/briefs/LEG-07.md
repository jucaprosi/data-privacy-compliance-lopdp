### LEG-07 · finales-de-linea-crlf-en-los-bat-para-que-cmd-lea-el-aviso  (tanda 93)

**Contexto.** Sala: `gobernanza`. Depende de: `ENT-01`, `LEG-06`, `MARCA-05`, `QA-02` (las cuatro hechas en `main`). Especificaciones: `governance/tareas/LEG-07.md` y `governance/especificaciones/LEG-07.md` (manda la especificación).

**Orden.** Va en paralelo con FE-29 (tanda 93): no comparten archivos. LEG-06 ya está hecha (#966).

**Origen.** Defecto de LEG-06 (#959): el aviso de autor quedó en los `.bat` con finales LF, y cmd imprime «© no se reconoce como un comando interno o externo» al arrancar cada uno.

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/leg-07`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/leg-07 origin/main`), en un worktree propio fuera del escritorio, en `C:/Users/Juan Carlos/worktrees-evydentia/leg-07`.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/LEG-07.md` y quita la línea `agente = "ninguno"`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Los seis `.bat` son de esta ficha.** Están en la `propiedad` de LEG-07 y son los únicos que esta tarea toca; el PR los revisa el CTO. Aunque figuran en la lista de archivos de gobernanza reservada del preámbulo, aquí se editan por la propiedad declarada en la ficha.
- **Contenido intacto.** Solo cambian los finales de línea. No cambies el texto del aviso ni `scripts/poner_aviso_de_autor.py`.
- **Entorno:** sin `.env`. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`, ni `data/biblioteca/**`.
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR.

**Objetivo** (en este orden):

1. `LEG-07` — Finales de línea CRLF en los .bat para que cmd lea el aviso de autor
   - `.gitattributes`: añade `*.bat text eol=crlf` y `*.cmd text eol=crlf`. Conserva `data/biblioteca/** -text` tal cual.
   - Renormaliza con `git add --renormalize` los seis `.bat` (`ejecutar_arnes_tres_pilares.bat`, `ejecutar_arnes_verificacion.bat`, `iniciar_backend.bat`, `iniciar_frontend.bat`, `iniciar_todo.bat`, `scripts/entorno.bat`) y comprueba que el diff solo cambia los finales de línea.
   - `tests/test_leg06_aviso_de_autor.py`: añade `test_bat_y_cmd_en_crlf` y `test_gitattributes_crlf_y_biblioteca` según §5 de la especificación.

**Rastro ¤**:

- `¤ip`, `¤arbitro`.

**Escribe** (lista exclusiva):

  - `.gitattributes`
  - `ejecutar_arnes_tres_pilares.bat`
  - `ejecutar_arnes_verificacion.bat`
  - `iniciar_backend.bat`
  - `iniciar_frontend.bat`
  - `iniciar_todo.bat`
  - `scripts/entorno.bat`
  - `tests/test_leg06_aviso_de_autor.py`

**No hagas:**

- No escribas fuera de la lista anterior.
- No cambies el contenido de los `.bat`, solo su final de línea.
- Cumple el contrato de la especificación; ante una contradicción con el PRD o las invariantes, detente e informa.
- No toques producción ni una base compartida; no despliegues.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `LEG-07`: pytest tests/test_leg06_aviso_de_autor.py; git ls-files --eol muestra i/crlf en los seis .bat; cada .bat arranca en cmd sin «no se reconoce como un comando»; reparto, índice y especificaciones con código 0; mutaciones m1 y m2.
- La comprobación en cmd de Windows la hace el ingeniero y anota la salida en el PR (es la prueba en físico de §5).
