# Validación local antes de VPS

## 1. Arrancar en modo rápido

Usa este modo para comprobar interfaz, email-gate, CRM e informe sin esperar a Codex:

```bash
PORT=8787 AI_PROVIDER=fallback ALLOW_AI_FALLBACK=true ./run_local_beta.sh
```

Abre:

```text
http://localhost:8787/Agente_Real_CRM.html
```

Comprueba:

- La página empieza sin pedir email.
- El gancho principal es `¿Dónde se te escapa tiempo, dinero o clientes?`.
- El posicionamiento visible incluye `Discovery gratuito`, `mini sesión consultiva` y `Empieza con una escena real`.
- El texto de apoyo transmite que hablas con un agente que analiza el negocio como lo haría un consultor.
- El botón visible es `Empezar diagnóstico`.
- La primera pantalla invita a contar el negocio en bruto y recomienda usar el micrófono, sin mencionar que al final se pedirá email.
- Aparece el bloque `Discovery en vivo` como preview de la experiencia.
- No aparecen textos como `JSON`, `CRM`, `fallback`, `informe potente` o lenguaje interno de producto.
- Al empezar aparece un panel vivo de discovery con lo que el agente está entendiendo, preguntas abiertas y oportunidades candidatas.
- La conversación no se siente como 5 preguntas fijas: debe repreguntar según el caso, pedir ejemplos cuando falte evidencia y avanzar cuando ya tenga suficiente.
- El botón `Generar informe` no aparece hasta que el agente decide que tiene suficiente.
- El email se pide solo antes de generar el diagnóstico.
- El email exige aceptar el uso de datos y enlaza a privacidad.
- El informe incluye `Resumen de acción`, `Matriz de priorización`, `Por qué esta va primero` y feedback al final.
- El informe evita frases vacías como `informe potente`: debe hablar de diagnóstico, oportunidades, empleado IA recomendado y primer paso.
- El CRM guarda email, conversación, outcome, `first_opportunity`, `first_step` y feedback.

Si ya tienes un servidor viejo en el puerto 8787 y quieres sustituirlo por la versión actual:

```bash
REPLACE=true ./run_local_beta.sh
```

## 2. Arrancar con Codex real

Usa este modo para probar calidad de conversación:

```bash
AI_PROVIDER=codex ./run_local_beta.sh
```

Cada turno puede tardar 9-20 segundos. El diagnóstico puede tardar 30-90 segundos.

## 3. Ejecutar pruebas de producto

Con el servidor arrancado:

```bash
python3 test_public_ui_flow.py --base http://localhost:8787
python3 test_public_report_flow.py --base http://localhost:8787
python3 test_session_restore_flow.py --base http://localhost:8787
```

Estas pruebas abren la página como escritorio y móvil, comprueban que el gancho inicial aparece pronto, que se puede empezar sin pedir email, que el estado de espera aparece mientras el agente prepara la respuesta, que el cierre genera email-gate, informe y feedback, y que una recarga no borra la sesión.

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
- `python3 launch_go_no_go.py --env /tmp/primer-empleado-valid.env --base http://localhost:8787 --mic-optional` devuelve `GO` solo para validación local/controlada.
- Para una validación más cercana a usuario real: `python3 release_check.py --env /tmp/primer-empleado-valid.env --base http://localhost:8787 --with-browser --with-transcription`.

Nota: el go/no-go público debe ejecutarse con `.env` real, contraseña CRM y URL HTTPS. Si lo lanzas contra `localhost` con `--public-beta`, tiene que devolver `NO_GO`.
