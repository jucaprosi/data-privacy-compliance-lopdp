# Variación del Arnés completo contra Neon
`¤ci-cd` `¤arbitro`

> Medido el 2026-11-02 con `scripts/medir_variacion_ci.py`, solo con corridas ya existentes de GitHub Actions. **Causa confirmada: la región de Azure donde GitHub coloca el ejecutor.** Explica el 97 % de la varianza de los segundos por prueba. No hay cambio del flujo ni de Neon en esta ficha: la decisión es del propietario (sección 4).

---

## 1. La causa

GitHub reparte cada trabajo de `ubuntu-latest` en una región de Azure de Estados Unidos o México, y la escribe en el registro. La misma suite tarda según la región que toque:

| Región | Corridas | Hacia `main` | Min (mín / mediana / máx) | s por prueba | Consulta (ms) | Sin base (ms) |
| :--- | ---: | ---: | :--- | ---: | ---: | ---: |
| northcentralus | 12 | 4 | 5.1 / 6.75 / 9.3 | 0.25 | 735 | 42.2 |
| eastus2 | 14 | 7 | 7.1 / 8.6 / 11.4 | 0.36 | 1043 | 36.5 |
| eastus | 31 | 9 | 6.2 / 9.0 / 12.7 | 0.39 | 1128 | 38.0 |
| centralus | 41 | 16 | 8.4 / 11.1 / 15.8 | 0.49 | 1414 | 34.1 |
| westcentralus | 12 | 5 | 13.1 / 15.6 / 17.9 | 0.66 | 1911 | 37.1 |
| southcentralus | 8 | 1 | 16.4 / 18.25 / 22.6 | 0.79 | 2347 | 35.1 |
| westus2 | 11 | 3 | 20.6 / 24.4 / 33.8 | 1.08 | 3182 | 36.5 |
| westus | 20 | 6 | 21.3 / 25.05 / 35.9 | 1.07 | 3156 | 38.0 |
| westus3 | 35 | 9 | 22.0 / 26.1 / 35.8 | 1.10 | 3284 | 34.4 |
| mexicocentral | 2 | 0 | 25.1 / 26.6 / 28.1 | 1.13 | 3393 | 33.0 |

Hay 186 corridas medibles entre el 2026-10-28 y el 2026-11-02, 60 de ellas hacia `main`. *Consulta* es la mediana de las pruebas de más de 100 ms en archivos que usan la base. *Sin base* es la media de las pruebas que no tocan la base.

- **La región explica el 97 % de la varianza** de los segundos por prueba: 97,1 % solo hacia `main` y 97,5 % en las 20 de `Arnés completo` con ese nombre.
- **El tiempo sube de este a oeste**, de 0,25 a 1,13 s por prueba. Las regiones del oeste llevan unos 26 min y `northcentralus`, 6,8 min.
- **No es la CPU del ejecutor.** Las pruebas sin base no se frenan: tardan de 33 a 42 ms en todas las regiones, sin relación con el tiempo por prueba (Spearman −0,11).
- **Es la red hasta Neon.** Solo se frenan las pruebas que consultan la base: de 735 a 3 393 ms.

## 2. Las cinco hipótesis

Para las hipótesis 1 y 5 cada corrida se compara con la mediana de su región, para aislarlas de la distancia.

| # | Hipótesis | Medición | Resultado |
| :--- | :--- | :--- | :--- |
| 1 | Corridas simultáneas sobre la misma rama | Hacia `main`: sin solapar, 1,00 veces la mediana de su región (35 corridas); solapadas, 1,00 (25). Spearman 0,00 con la misma rama y 0,00 con otras | **Descartada** |
| 2 | Arranque en frío de Neon | Hacia `main`: primera consulta tras 10 min o más de reposo, 3,1 s de mediana (máximo 6,4 s); con menos reposo, 1,9 s | **Real, pero irrelevante**: unos segundos en corridas de hasta 36 min |
| 3 | Cómputo de la rama de Neon y su plan | Solo se ve en la consola | **No verificado**. Lo aporta el propietario |
| 4 | Distancia entre el ejecutor y Neon | Sección 1 | **Confirmada**, 97 % de la varianza |
| 5 | Hora del día y cola de Neon | Spearman 0,02 con la hora UTC hacia `main`; por franjas de 6 horas, medianas de 0,90 a 1,00 | **Hora descartada**. La cola de Neon no se puede observar desde aquí |

**Sobre la hipótesis 1.** La medición del 2026-10-31 («tres a la vez tardan casi el triple») no se reproduce. No consta que esa medición comparara la región, y un ejecutor del oeste frente a uno del este ya da una razón de ese tamaño. Por eso conviene revisar `scripts/esperar_turno_neon.py`: esperar turno no acorta la corrida según estos datos. Si no hace falta por otro motivo, se puede retirar.

**Lo que queda sin explicar.** Dentro de una región, el 90 % de las corridas está entre 0,85 y 1,21 veces su mediana. La hipótesis 3 podría aportar algo ahí, pero no la diferencia entre regiones: el cómputo de Neon no sabe dónde está el ejecutor.

## 3. Lo que no se pudo medir

| Dato | Estado | Quién lo aporta |
| :--- | :--- | :--- |
| Región de Neon del proyecto | **No verificado.** Las corridas más rápidas apuntan al este de Estados Unidos, pero es una inferencia | El propietario, en la consola de Neon |
| Tamaño de cómputo, escalado y tiempo de suspensión de `test-main` | **No verificado** | El propietario, en la consola de Neon |
| Plan de Neon | **No verificado** | El propietario, en la consola de Neon |
| Latencia de ida y vuelta de una consulta | **No medida.** El registro da tiempo por prueba, no por consulta | Otra ficha, sin clave de Neon en esta |
| Consultas por prueba | **No medidas.** Ver la ficha propuesta en `MEDICION_PRUEBAS_LENTAS.md` | Esa ficha |
| Cola de Neon | **No observable** desde GitHub Actions | Nadie, por ahora |

## 4. Cambio propuesto y efecto esperado

Hoy, con 1 800 pruebas y el reparto medido, Pytest tarda 21 min de media; en el oeste, unos 33 min. Tres de cada diez corridas hacia `main` (18 de 60) superan los 20 min.

| Opción | Efecto esperado | Coste o límite |
| :--- | :--- | :--- |
| **A. Reducir consultas por prueba** | Proporcional a lo que se quite, y mayor en el oeste. No se puede estimar sin contar consultas | Trabajo en las pruebas, sin coste de infraestructura |
| B. Ejecutor propio cerca de Neon | Todas las corridas cerca de 7 a 11 min | Mantener una máquina. El repositorio es **público**: un ejecutor propio solo debe atender corridas de confianza |
| C. Ejecutor grande con red privada de Azure en una región fija | El mismo que B | Exige plan Team o Enterprise de una **organización**; el repositorio es de una cuenta personal |
| D. Mover Neon de región | **No sirve:** los ejecutores se reparten por todo el país, así que siempre habría regiones lejanas | Exige proyecto nuevo y cambiar todas las URL |
| E. Menos pruebas contra Neon hacia `main` | Proporcional a lo que pase al contenedor | Cambia la regla del Arnés completo obligatorio: lo decide el propietario |

**Recomendación:** la opción A, que no cuesta infraestructura ni cambia las reglas, y aceptar por ahora una corrida de hasta 36 min, que no falla por esto. Las opciones B y E son decisiones del propietario. Descartar `concurrency` por rama de Neon como solución: el solapamiento no influye.

**Fichas propuestas:**

1. Contar consultas por prueba en los archivos que señala `MEDICION_PRUEBAS_LENTAS.md`.
2. Revisar si `scripts/esperar_turno_neon.py` sigue haciendo falta.

Fuentes de los límites: [ejecutores grandes](https://docs.github.com/en/actions/concepts/runners/larger-runners), [red privada de Azure](https://docs.github.com/en/organizations/managing-organization-settings/about-azure-private-networking-for-github-hosted-runners-in-your-organization) y [región de un proyecto de Neon](https://neon.com/faqs/change-project-region).

## 5. Cómo repetir la medición

```powershell
python scripts/medir_variacion_ci.py --corridas 300 --salida tabla.md --json datos.json
```

Solo lee GitHub Actions y necesita `gh` con sesión iniciada. Los registros caducan, así que las corridas antiguas pueden quedar sin datos.

## 6. Corridas hacia `main`

| Corrida | Inicio (UTC) | Rama Neon | Hacia `main` | Región | Min | Pruebas | Consulta (ms) | Sin base (ms) | Primera consulta (s) | Reposo (min) | Solapadas misma rama | Solapadas otra rama |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 41532910057 | 2026-11-02 21:58 | `test-main` | sí | westus2 | 33.6 | 1800 | 3183.8 | 48.7 | 4.91 | 304.8 | 0 | 0 |
| 41488840100 | 2026-11-02 17:16 | `test-juan-carlos` | sí | eastus | 12.5 | 1753 | 1216.8 | 48.6 | 1.41 | 37.5 | 0 | 0 |
| 41479331361 | 2026-11-02 16:17 | `test-main` | sí | westus | 35.9 | 1752 | 3550.6 | 48.8 | 4.34 | 19.5 | 0 | 1 |
| 41474982353 | 2026-11-02 15:51 | `test-juan-carlos` | sí | northcentralus | 9.3 | 1752 | 886.1 | 48.9 | 0.64 | 8.4 | 0 | 1 |
| 41446452507 | 2026-11-02 15:51 | `test-main` | sí | northcentralus | 7.1 | 1710 | 699.6 | 50.2 | 1.52 | 1062.1 | 0 | 1 |
| 41396330532 | 2026-11-02 05:54 | `test-juan-carlos` | sí | eastus | 9.3 | 1704 | 1010.3 | 46.7 | 0.96 | 4.0 | 0 | 0 |
| 41382981455 | 2026-11-02 03:26 | `test-juan-carlos` | sí | northcentralus | 8.1 | 1607 | 927.6 | 45.1 | 0.65 | 2.2 | 0 | 0 |
| 41379630466 | 2026-11-02 02:57 | `test-juan-carlos` | sí | centralus | 13.3 | 1607 | 1410.6 | 45.3 | 2.17 | 1.6 | 0 | 2 |
| 41358298313 | 2026-11-01 22:42 | `test-juan-carlos` | sí | westus | 28.0 | 1584 | 3164.5 | 45.8 | 4.66 | 288.6 | 0 | 0 |
| 41350268991 | 2026-11-01 21:58 | `test-main` | sí | eastus | 10.9 | 1584 | 1216.2 | 47.9 | 2.21 | 238.8 | 0 | 0 |
| 41303828615 | 2026-11-01 17:30 | `test-main` | sí | westus3 | 28.4 | 1559 | 3283.3 | 46.2 | 5.78 | 1251.3 | 0 | 1 |
| 41331208473 | 2026-11-01 17:24 | `test-juan-carlos` | sí | westus | 28.5 | 1584 | 3235.2 | 46.4 | 4.81 | 302.8 | 0 | 1 |
| 41302669882 | 2026-11-01 11:38 | `test-juan-carlos` | sí | centralus | 11.6 | 1559 | 1377.0 | 35.4 | 2.34 | 361.3 | 0 | 0 |
| 41264556782 | 2026-11-01 02:18 | `test-juan-carlos` | sí | southcentralus | 18.4 | 1531 | 2292.9 | 35.8 | 3.73 | 158.6 | 0 | 2 |
| 41252523024 | 2026-10-31 23:27 | `test-juan-carlos` | sí | centralus | 12.6 | 1531 | 1601.3 | 36.2 | 1.22 | 4.5 | 0 | 0 |
| 41245597279 | 2026-10-31 21:54 | `test-juan-carlos` | sí | westus3 | 26.1 | 1531 | 3306.7 | 41.7 | 6.12 | 119.8 | 0 | 0 |
| 41237785238 | 2026-10-31 20:13 | `test-main` | sí | westus | 25.8 | 1531 | 3248.4 | 45.1 | 5.03 | 128.9 | 0 | 2 |
| 41233175845 | 2026-10-31 19:41 | `test-juan-carlos` | sí | centralus | 13.3 | 1531 | 1697.6 | 32.8 | 1.87 | 1.5 | 0 | 3 |
| 41233172766 | 2026-10-31 19:15 | `test-juan-carlos` | sí | westus | 24.4 | 1531 | 3042.3 | 45.9 | 3.3 | 1.7 | 0 | 4 |
| 41173727282 | 2026-10-31 05:44 | `test-juan-carlos` | sí | eastus | 9.2 | 1507 | 1088.1 | 49.4 | 1.33 | 2.9 | 1 | 0 |
| 41171414673 | 2026-10-31 05:10 | `test-juan-carlos` | sí | westus3 | 26.1 | 1464 | 3261.8 | 39.2 | 3.6 | 12.9 | 3 | 2 |
| 41171388049 | 2026-10-31 05:09 | `test-juan-carlos` | sí | eastus2 | 8.7 | 1451 | 1035.0 | 49.5 | 1.24 | 12.7 | 3 | 1 |
| 41171366469 | 2026-10-31 05:09 | `test-juan-carlos` | sí | westus3 | 26.4 | 1437 | 3340.8 | 41.5 | 4.9 | 12.2 | 3 | 2 |
| 41169404854 | 2026-10-31 04:40 | `test-juan-carlos` | sí | westcentralus | 15.6 | 1437 | 1912.0 | 56.7 | 2.16 | 1.1 | 3 | 2 |
| 41167150037 | 2026-10-31 04:07 | `test-juan-carlos` | sí | westus3 | 26.2 | 1435 | 3331.3 | 39.5 | 3.54 | 2.9 | 4 | 1 |
| 41145114805 | 2026-10-30 23:33 | `test-juan-carlos` | sí | eastus | 9.6 | 1411 | 1164.5 | 37.8 | 1.3 | 3.2 | 0 | 0 |
| 41128072471 | 2026-10-30 21:04 | `test-main` | sí | eastus | 6.9 | 1400 | 845.3 | 37.3 | 1.9 | 396.5 | 0 | 0 |
| 41126282941 | 2026-10-30 20:50 | `test-juan-carlos` | sí | centralus | 12.3 | 1400 | 1534.7 | 35.1 | 1.23 | 41.8 | 0 | 0 |
| 41118778236 | 2026-10-30 19:53 | `test-juan-carlos` | sí | northcentralus | 5.5 | 1400 | 655.1 | 31.0 | 0.78 | 38.5 | 2 | 0 |
| 41118749425 | 2026-10-30 19:53 | `test-juan-carlos` | sí | westcentralus | 15.4 | 1400 | 1910.5 | 40.0 | 2.31 | 38.5 | 2 | 0 |
| 41118723178 | 2026-10-30 19:52 | `test-juan-carlos` | sí | westcentralus | 15.0 | 1400 | 1841.9 | 37.7 | 3.07 | 38.4 | 2 | 0 |
| 41103367020 | 2026-10-30 18:02 | `test-juan-carlos` | sí | centralus | 10.5 | 1393 | 1353.6 | 35.2 | 3.2 | 174.8 | 0 | 0 |
| 41074511912 | 2026-10-30 14:46 | `test-juan-carlos` | sí | centralus | 9.9 | 1382 | 1286.7 | 29.9 | 2.23 | 31.1 | 0 | 0 |
| 41070451595 | 2026-10-30 14:17 | `test-main` | sí | eastus2 | 10.2 | 1339 | 1298.7 | 35.7 | 3.41 | 29.2 | 0 | 0 |
| 41065212176 | 2026-10-30 13:41 | `test-main` | sí | eastus | 6.8 | 1339 | 858.6 | 39.3 | 2.97 | 592.2 | 0 | 1 |
| 40997210505 | 2026-10-30 03:25 | `test-main` | sí | westus3 | 24.2 | 1325 | 3258.9 | 28.9 | 3.62 | 3.3 | 0 | 0 |
| 40979590867 | 2026-10-30 00:26 | `test-main` | sí | westus | 23.2 | 1325 | 3052.2 | 37.6 | 5.04 | 57.8 | 0 | 3 |
| 40971585693 | 2026-10-29 23:13 | `test-main` | sí | westcentralus | 14.6 | 1325 | 1897.7 | 36.1 | 4.06 | 63.5 | 0 | 1 |
| 40959125157 | 2026-10-29 22:40 | `test-juan-carlos` | sí | eastus | 8.8 | 1325 | 1127.9 | 35.0 | 0.27 | 36.1 | 0 | 0 |
| 40962592658 | 2026-10-29 22:02 | `test-main` | sí | eastus2 | 8.1 | 1325 | 1050.4 | 36.1 | 1.1 | 98.7 | 0 | 1 |
| 40958210669 | 2026-10-29 21:30 | `test-juan-carlos` | sí | centralus | 10.6 | 1325 | 1366.2 | 35.2 | 1.26 | 189.2 | 2 | 0 |
| 40958206450 | 2026-10-29 21:30 | `test-juan-carlos` | sí | westus2 | 24.4 | 1325 | 3193.2 | 36.7 | 3.29 | 189.2 | 2 | 0 |
| 40958077203 | 2026-10-29 21:29 | `test-juan-carlos` | sí | centralus | 11.0 | 1325 | 1404.7 | 37.1 | 3.05 | 188.1 | 2 | 0 |
| 40944876947 | 2026-10-29 19:59 | `test-main` | sí | westus3 | 24.3 | 1325 | 3225.7 | 32.9 | 6.41 | 107.4 | 0 | 0 |
| 40926381449 | 2026-10-29 17:59 | `test-juan-carlos` | sí | westus3 | 22.0 | 1279 | 3138.7 | 29.7 | 3.47 | - | 0 | 1 |
| 40923363948 | 2026-10-29 17:39 | `test-main` | sí | centralus | 10.4 | 1279 | 1381.8 | 35.1 | 1.38 | 2.6 | 2 | 0 |
| 40919200791 | 2026-10-29 17:14 | `test-main` | sí | centralus | 10.7 | 1279 | 1456.6 | 33.9 | 2.6 | 1.7 | 3 | 0 |
| 40913852636 | 2026-10-29 16:40 | `test-main` | sí | centralus | 12.5 | 1279 | 1778.3 | 29.8 | 5.27 | 12.4 | 2 | 0 |
| 40909431696 | 2026-10-29 16:14 | `test-main` | sí | eastus2 | 7.1 | 1279 | 980.3 | 36.0 | 3.12 | 29.8 | 3 | 0 |
| 40901048493 | 2026-10-29 15:23 | `test-main` | sí | centralus | 11.7 | 1279 | 1618.2 | 29.7 | 1.94 | 8.8 | 7 | 0 |
| 40895151918 | 2026-10-29 14:49 | `test-main` | sí | westus2 | 21.9 | 1279 | 3116.3 | 30.4 | 3.35 | 7.3 | 3 | 0 |
| 40891422334 | 2026-10-29 14:26 | `test-main` | sí | eastus | 6.2 | 1279 | 826.7 | 38.7 | 2.58 | 23.3 | 1 | 0 |
| 40825445147 | 2026-10-29 05:48 | `test-main` | sí | centralus | 9.0 | 1241 | 1245.9 | 35.9 | 2.96 | 11.8 | 0 | 0 |
| 40816540329 | 2026-10-29 04:14 | `test-main` | sí | eastus2 | 11.4 | 1241 | 1517.1 | 37.8 | 1.57 | 2.1 | 3 | 0 |
| 40815507049 | 2026-10-29 04:03 | `test-main` | sí | westus3 | 22.4 | 1241 | 3177.9 | 33.0 | 3.55 | 3.7 | 4 | 0 |
| 40813104442 | 2026-10-29 03:37 | `test-main` | sí | centralus | 12.4 | 1241 | 1288.4 | 33.2 | 3.39 | 11.2 | 1 | 0 |
| 40809932994 | 2026-10-29 03:04 | `test-main` | sí | eastus2 | 7.3 | 1241 | 972.2 | 37.5 | 1.08 | 10.6 | 2 | 0 |
| 40790707420 | 2026-10-28 23:57 | `test-main` | sí | westcentralus | 13.1 | 1241 | 1830.4 | 34.2 | 2.29 | 63.0 | 1 | 0 |
| 40790677467 | 2026-10-28 23:56 | `test-main` | sí | eastus2 | 7.5 | 1241 | 1014.1 | 34.9 | 2.96 | 62.7 | 1 | 0 |
| 40777633235 | 2026-10-28 22:09 | `test-main` | sí | centralus | 9.0 | 1241 | 1235.7 | 35.2 | 1.79 | 4.4 | 0 | 0 |
