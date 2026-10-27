# BIBLIOTECA PMV — Notas de entrega

Backend y frontend dejan aquí una nota corta al terminar su parte de cada documento (BIB-001…BIB-012).
La especificación está en [`biblioteca-pmv.md`](biblioteca-pmv.md).

Reglas:

- Una entrada por documento y por capa. La más reciente va arriba.
- No incluyas credenciales, URL de bases de datos, tokens ni datos reales de personas. Usa solo la organización de prueba y datos ficticios.
- Si algo queda pendiente, dilo en la nota. No lo marques como hecho.
- Informa el CI solo cuando terminen todos los checks. Si no, escribe «X de Y terminados, N en curso».

## Plantilla de nota

```markdown
### BIB-00X · <nombre> · <backend | frontend> · AAAA-MM-DD
- **Qué se hizo:** …
- **Endpoints / pantallas:** `GET /api/v1/biblioteca/…` · pestaña / panel …
- **Datos de prueba:** organización de prueba «…» (ficticia); usuario con rol …; cómo cargarlos: `…`
- **Cómo verlo:** 1) … 2) … 3) …
- **Pruebas:** `pytest …` / `npx playwright test …` — resultado; CI: X de Y terminados
- **Commit / PR:** `abc1234` · #NNN
- **Pendiente:** … (o «nada»)
```

## Entregas

_Aún no hay entregas._
