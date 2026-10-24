# Mutación QA-08: purga omitida

La mutación se ejecutó en una copia aislada del frontend, fuera del repositorio.
En `src/store/useAuditStore.ts`, dentro de `setNormativa`, se sustituyeron estas
tres líneas:

```ts
archivosCargados: cambioNorma ? [] : state.archivosCargados,
evidencias: cambioNorma ? [] : state.evidencias,
propuestasIA: cambioNorma ? {} : state.propuestasIA,
```

por:

```ts
archivosCargados: state.archivosCargados,
evidencias: state.evidencias,
propuestasIA: state.propuestasIA,
```

Comando ejecutado contra la copia mutada:

```powershell
$env:PLAYWRIGHT_BASE_URL='http://127.0.0.1:3001'
.\node_modules\.bin\playwright.cmd test --config tests/purga/playwright.config.ts --grep "cancelar conserva" --reporter=line
```

Resultado esperado y observado: código `1`, `1 failed`. La aserción de la línea
89 esperaba cero coincidencias para `politica-privacidad.pdf` tras confirmar el
cambio a NIIF, pero recibió una. Esto demuestra que el caso principal falla si
no se ejecuta la purga.
