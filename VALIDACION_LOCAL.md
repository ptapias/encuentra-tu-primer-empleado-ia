# Validación local antes de VPS

## 1. Arrancar en modo rápido

Usa este modo para comprobar interfaz, email-gate, CRM e informe sin esperar a Codex:

```bash
AI_PROVIDER=fallback HOST=localhost PORT=8787 python3 app_server.py
```

Abre:

```text
http://localhost:8787/Agente_Real_CRM.html?v=discovery
```

Comprueba:

- La página empieza sin pedir email.
- El botón visible es `Analizar mi negocio`.
- No aparecen textos como `JSON`, `CRM`, `fallback` o `informe potente`.
- Al empezar aparece `Lo que estoy entendiendo`.
- El botón `Generar informe` no aparece hasta que el agente decide que tiene suficiente.
- El email se pide solo antes de generar el diagnóstico.
- El email exige aceptar el uso de datos y enlaza a privacidad.
- El informe incluye `Matriz de priorización`, `Por qué esta va primero` y feedback al final.

## 2. Arrancar con Codex real

Usa este modo para probar calidad de conversación:

```bash
AI_PROVIDER=codex HOST=localhost PORT=8787 python3 app_server.py
```

Cada turno puede tardar 9-20 segundos. El diagnóstico puede tardar 30-90 segundos.

## 3. Ejecutar pruebas de producto

Con el servidor arrancado:

```bash
python3 test_public_ui_flow.py --base http://localhost:8787
python3 test_public_report_flow.py --base http://localhost:8787
```

Estas pruebas abren la página como escritorio y móvil, comprueban que el gancho inicial aparece pronto, que se puede empezar sin pedir email, que el estado de espera aparece mientras el agente prepara la respuesta y que el cierre genera email-gate, informe y feedback.

Si quieres probar la transcripción con audio real generado localmente:

```bash
python3 test_transcription_local.py --base http://localhost:8787
```

Esta prueba no sustituye la prueba manual de permisos del micrófono en navegador, pero confirma que `/transcribe` procesa un audio real y devuelve texto.

Después valida la calidad del agente real:

```bash
python3 test_discovery_flow.py
```

El script simula:

- clínica dental,
- inmobiliaria,
- consultor B2B.

La prueba falla si el agente no devuelve:

- respuesta natural,
- foco actual,
- gaps abiertos,
- insights vivos,
- procesos candidatos,
- diagnóstico con empleado recomendado,
- oportunidades,
- `ready_for_report=true` cuando ya hay evidencia suficiente,
- plan de 7 días.

## 4. Criterio mínimo para pasar a VPS

Antes de subirlo:

- 3 casos del script pasan.
- 2 pruebas manuales con voz pasan.
- El CRM interno muestra conversación, diagnóstico y feedback.
- No hay textos internos en la página pública.
- Codex CLI funciona en la máquina destino o se decide usar API.
- `python3 test_public_ui_flow.py --base http://localhost:8787` pasa.
- `python3 release_check.py --env /tmp/primer-empleado-valid.env --base http://localhost:8787` pasa en local.
- Para una validación más cercana a usuario real: `python3 release_check.py --env /tmp/primer-empleado-valid.env --base http://localhost:8787 --with-browser --with-transcription`.
