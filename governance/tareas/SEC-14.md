+++
id = "SEC-14"
titulo = "Empaquetado seguro del frontend: sin mapas de fuente públicos y sin secretos en el paquete del navegador"
ola = "C"
estado = "pendiente"
sala = "frontend, pruebas"
depende_de = ["GCP-03"]
propiedad = ["scripts/verificar_empaquetado_frontend.py", "frontend/variables_publicas.json", "tests/test_sec14_empaquetado_frontend.py"]
arbitro = "pytest tests/test_sec14_empaquetado_frontend.py + suite completa + vigilantes"
rastros = ["¤seguridad", "¤frontend-ide"]
+++
# SEC-14 · Empaquetado seguro del frontend: sin mapas de fuente públicos y sin secretos en el paquete del navegador

## Entrega
- Lista blanca `frontend/variables_publicas.json` con las únicas variables `NEXT_PUBLIC_*` que pueden llegar al navegador y el motivo de cada una.
- Verificador `scripts/verificar_empaquetado_frontend.py` que inspecciona la configuración de Next.js (sin `productionBrowserSourceMaps`) y, sobre la salida de `next build`, rechaza archivos `*.map` servibles bajo `/_next/static/`, variables públicas fuera de la lista blanca y cadenas con forma de clave privada, token o URL de base de datos.

## Pruebas
- `pytest tests/test_sec14_empaquetado_frontend.py` comprueba con compilaciones de ejemplo que el verificador detecta un `.map` publicado, una variable pública no declarada y una clave incrustada, y que acepta la configuración real del repositorio (`INV_FRONTEND_NO_PUBLIC_SOURCE_MAPS_NO_SECRETS`).
