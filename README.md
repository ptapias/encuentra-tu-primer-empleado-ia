# Encuentra Tu Primer Empleado IA

MVP estratégico y operativo para convertir audiencia de YouTube/newsletter en leads cualificados para:

- Newsletter de IA al Día.
- Lista de espera/cohort de agentes IA para personas no técnicas.
- Aprendizaje de mercado mediante feedback al final del diagnóstico.
- Implementaciones de empleados IA.
- Llamadas comerciales solo cuando hay encaje, urgencia y presupuesto.

## Archivos

- `Sistema_Completo.md`: documento principal de estrategia, producto, agente, scoring, funnel, copy, arquitectura y plan de implementación.
- `MVP_Conversacional_Codex.md`: rediseño del MVP como entrevista real en lenguaje natural y explicación honesta de Codex/API.
- `Prompt_Investigacion_Procesos.md`: prompt de fondo para el agente investigador de procesos automatizables.
- `Prompt_Agente_Diagnostico.md`: prompt listo para usar en un agente conversacional.
- `Scoring_y_CRM.csv`: criterios de scoring y campos internos recomendados.
- `Agente_Real_CRM.html`: versión nueva con agente conectado a backend, CRM SQLite, micrófono, diagnóstico accionable, matriz visual de decisión y feedback.
- `CRM_Dashboard.html`: dashboard interno para revisar métricas de embudo, utilidad media del feedback, patrones de faltantes, filtrar leads por oferta/estado/origen, ver conversación, outcome, oferta recomendada, consentimiento, interés en CTA, feedback estructurado, cambiar estado/oferta manualmente y exportar CSV.
- `app_server.py`: servidor local con endpoints `/api/session`, `/api/chat`, `/api/report`, `/api/feedback`, `/api/leads`, `/api/lead`, `/api/metrics`, `/api/export.csv` y `/transcribe`.
- `MVP_Final_Roadmap.md`: definición de versión enseñable/vendible, brechas y tramos de ejecución.
- `DEPLOYMENT_VPS.md`: guía para desplegar en VPS con Codex CLI, systemd y Caddy.
- `VPS_LAUNCH_PACKET.md`: checklist operativo con datos necesarios, comandos, validación, prueba manual y criterios para abrir tráfico.
- `MANUAL_PRODUCTION_TEST.md`: plantilla de aceptación manual para probar escritorio, móvil, micrófono HTTPS, informe, CRM, CSV y go/no-go antes de testers.
- `PRODUCTION_READINESS.md`: lista corta de datos, variables, legal, gate final y prueba manual antes de abrir la beta.
- `deploy/install_vps.sh`: instalador con guardarraíles para crear `.env`, copiar servicios, activar backups y validar smoke test en el VPS.
- `deploy/verify_vps.sh`: verificador de VPS con smoke local/HTTPS, release gate y checks opcionales de navegador/transcripción.
- `deploy/primer-empleado-ia-backup.service` y `deploy/primer-empleado-ia-backup.timer`: unidades systemd para backup diario del CRM en VPS.
- `VALIDACION_LOCAL.md`: checklist para probar experiencia, agente, email-gate, informe y CRM antes del VPS.
- `BETA_TEST_PLAN.md`: plan para reclutar testers, medir calidad del diagnóstico y decidir si la beta está lista para abrir más tráfico.
- `COMPLETION_AUDIT.md`: auditoría requisito por requisito del estado real frente al objetivo Ontora-lite.
- `PRIVACY_BETA.md`: nota operativa de privacidad para la beta, con información básica y pendientes antes de tráfico público.
- `PRIVACY_BETA.html`: página pública de privacidad enlazada desde el diagnóstico.
- `test_discovery_flow.py`: prueba de producto con casos de clínica dental, inmobiliaria y consultor B2B.
- `test_beta_smoke.py`: prueba rápida post-despliegue para comprobar salud, página pública, sesión y protección de métricas/CRM.
- `test_public_ui_flow.py`: prueba de navegador para validar gancho inicial, móvil, arranque sin email y estado de espera del agente.
- `test_public_report_flow.py`: prueba de navegador del cierre completo: agente listo, email final, informe renderizado y feedback.
- `test_session_restore_flow.py`: prueba de navegador para recuperar una sesión a mitad de discovery o lista para informe tras recargar.
- `test_transcription_local.py`: prueba local opcional que genera audio real, lo manda a `/transcribe` y comprueba que vuelve texto.
- `preflight_vps.py`: comprobación previa de VPS para validar `.env`, proveedor IA, auth, permisos y binarios antes de arrancar systemd.
- `release_check.py`: chequeo agrupado de release para validar sintaxis, copy público, privacidad beta, preflight y smoke test antes de abrir la beta.
- `release_check.py --with-browser --with-transcription`: añade pruebas de navegador y audio real contra una URL local o VPS ya arrancada.
- `release_check.py --public-beta`: gate estricto para VPS público; exige HTTPS, credenciales CRM, privacidad final y proveedor IA verificado.
- `launch_go_no_go.py`: veredicto operativo final antes de enseñar la beta, combinando release check, navegador/transcripción y confirmaciones manuales.
- `test_public_beta_gate.py`: prueba unitaria del gate público para no abrir por error en localhost, sin HTTPS o con credenciales incorrectas.
- `test_ai_concurrency.py`: prueba rápida de que el backend devuelve agente ocupado cuando no hay hueco de IA disponible.
- `test_agent_quality_guard.py`: prueba de calidad conversacional para evitar que el agente repita una petición cuando el usuario ya dio un ejemplo o se frustra.
- `test_server_guards.py`: prueba de guardas básicos del servidor como rate limit e emails inválidos.
- `sync_crm_webhook.py`: sincronizador manual para reenviar leads existentes al CRM externo si se configura el webhook después o hay que reintentar.
- `test_crm_webhook_sync.py`: prueba de integración del sincronizador con un receptor webhook local.
- `test_backup_crm.py`: prueba de backup SQLite/JSONL en un entorno temporal.
- `backup_crm.py`: copia segura de `crm.sqlite3` y `crm_leads.jsonl` para operación de beta.
- `.env.example`: configuración de proveedor IA, límites, puerto y contraseña del CRM.
- `Prototipo_Conversacional.html`: prototipo principal de chat conversacional con repreguntas, memoria, informe preliminar y feedback.
- `Prototipo_Diagnostico.html`: prototipo antiguo tipo formulario. Mantener solo como referencia secundaria.
- `Plan_Prueba_y_Hosting.md`: cómo probarlo, publicarlo gratis al inicio y qué hacer con la parte de Codex/API.

## Recomendación de lanzamiento

Lanzar primero la versión gratuita como experiencia conversacional adaptativa: el usuario empieza sin registro, habla en lenguaje natural, el agente decide la siguiente pregunta según lo que falta por entender, detecta procesos y pide el email solo al final para entregar el informe. Objetivo normal: 7-10 minutos; puede alargarse a 12-15 preguntas si el caso lo necesita.

La versión actual incluye grabación por micrófono con transcripción local vía Whisper cuando se sirve con `app_server.py`, indicador de fase, matriz de evaluación basada en el framework `AI Use Case Evaluation Framework v0.2` e informe con iniciativas priorizadas. El informe explica por qué una oportunidad va primero, muestra las señales concretas que sostienen la recomendación, enseña un flujo práctico de cómo trabajaría el empleado IA y permite guardar/imprimir PDF antes de pasar al plan de 7/30 días.

## Probar la versión real

Para arrancar la versión con agente + CRM:

```bash
python3 app_server.py
```

Luego abre:

- Agente: `http://localhost:8787/Agente_Real_CRM.html`
- CRM interno: `http://localhost:8787/CRM_Dashboard.html`
- Prototipo anterior: `http://localhost:8787/Prototipo_Conversacional.html`

Por defecto el backend intenta usar `AI_PROVIDER=codex`, que llama a Codex CLI autenticado localmente con tu cuenta de ChatGPT/Codex. Esto sirve para pruebas internas en tu máquina o en un servidor donde hayas iniciado sesión con Codex CLI. No es la vía recomendada para una web pública con tráfico abierto.

En pruebas locales, un turno de conversación con Codex CLI tarda alrededor de 9-15 segundos y un informe puede tardar 30-60 segundos. Es suficiente para validar internamente el producto y enseñar demos controladas, pero conviene medirlo antes de abrirlo a mucho tráfico.

En beta con Codex CLI, el backend limita por defecto la IA a un diagnóstico concurrente (`MAX_AI_CONCURRENCY=1`). Si dos personas piden respuesta a la vez, la segunda espera unos segundos y, si no hay hueco, recibe un mensaje de reintento en lugar de lanzar procesos ilimitados en el VPS.

La beta también arranca con `BETA_NOINDEX=true`: sirve `robots.txt` con `Disallow: /` y añade `X-Robots-Tag: noindex, nofollow` para evitar indexación accidental mientras se valida el producto y la privacidad.

También puedes usar:

```bash
AI_PROVIDER=openai OPENAI_API_KEY=... python3 app_server.py
AI_PROVIDER=fallback python3 app_server.py
```

Para validar el producto antes del VPS:

```bash
python3 test_public_ui_flow.py --base http://localhost:8787
python3 test_discovery_flow.py
```

Checklist completo en `VALIDACION_LOCAL.md`.

Para pruebas puedes usar `AI_PROVIDER=fallback` o `ALLOW_AI_FALLBACK=true`. Para beta pública deja `ALLOW_AI_FALLBACK=false`: si Codex/OpenAI fallan, es mejor mostrar un error honesto que entregar un diagnóstico mediocre.

Los leads se guardan en `crm.sqlite3` y el evento de informe también se duplica en `crm_leads.jsonl` como respaldo local. Ambos archivos están fuera de Git.

La app guarda atribución básica si el enlace incluye parámetros como `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `video` o `ref`. Ejemplo para YouTube: `/Agente_Real_CRM.html?utm_source=youtube&utm_campaign=whatsapp_ia&video=agente-whatsapp`. El origen aparece en CRM, métricas y CSV.

Desde `CRM_Dashboard.html` puedes operar la beta sin tocar la base de datos: seleccionar un lead, cambiar su estado, ajustar la oferta recomendada, añadir notas internas, revisar qué gustó/faltó del diagnóstico, detectar objeciones/ideas de contenido y borrar un lead completo si alguien pide eliminar sus datos. Los cambios quedan registrados como evento interno cuando procede.

Si quieres conectar un CRM externo sin tocar código, configura `CRM_WEBHOOK_URL` en `.env`. La app enviará eventos de email capturado, informe generado, interés en CTA y feedback a Make, n8n, Zapier, Airtable, HubSpot o el destino que elijas. `CRM_WEBHOOK_SECRET` añade una cabecera sencilla para validar el origen.

Si activas el CRM externo después de tener leads o necesitas reintentar una sincronización, puedes reenviar snapshots de los leads existentes:

```bash
CRM_WEBHOOK_URL=https://hook.example.com CRM_WEBHOOK_SECRET=... python3 sync_crm_webhook.py --limit 100
```

Para probar el volumen sin enviar nada:

```bash
python3 sync_crm_webhook.py --dry-run --limit 20
```

Pulsa el icono de micrófono para grabar, vuelve a pulsarlo para transcribir con Whisper local y añadir el texto al campo. En VPS, define `WHISPER_BIN` y `FFMPEG_BIN` si no están en el `PATH`; si faltan, la app desactiva el micro y mantiene el flujo por texto.

## Producción beta

Para enseñarlo a público real, usa `.env.example` como base y define `ADMIN_PASSWORD` para proteger el CRM. La página pública ya no muestra leads internos; el dashboard queda separado en `CRM_Dashboard.html`.

La beta genera el informe en pantalla y guarda el lead en CRM. Todavía no envía emails automáticamente; si quieres entrega por correo habrá que conectar Resend, Beehiiv, ConvertKit u otro proveedor.

La guía de VPS está en `DEPLOYMENT_VPS.md`.

Nota clave: una web pública no puede usar directamente tu suscripción personal de Codex como API. Sí puedes usar Codex para pruebas locales o para procesar manualmente conversaciones recogidas por la web durante la validación.
