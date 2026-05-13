# Completion audit - Ontora-lite para pymes

Fecha de auditoría: 2026-05-13

Objetivo auditado:

Construir una versión "Ontora-lite" para pymes españolas de "Encuentra Tu Primer Empleado IA": un agente de discovery adaptativo que entrevista en lenguaje natural, entiende procesos reales, muestra progreso e insights vivos, genera un diagnóstico accionable y vendible, guarda leads en CRM y queda listo para beta pública en VPS con una experiencia visual y funcional comparable a una startup YC, sin preguntas predefinidas ni UX mediocre.

## Criterios concretos de éxito

1. La app pública permite iniciar un diagnóstico sin formulario previo.
2. El agente conversa en lenguaje natural y adapta sus preguntas a cada respuesta.
3. El agente entiende negocio, procesos, herramientas, impacto, riesgos y datos disponibles.
4. La UI muestra progreso, foco actual, insights vivos y gaps.
5. El usuario puede dictar por micrófono.
6. El email se pide solo al final, antes de entregar el informe.
7. El informe final es accionable: empleado IA recomendado, oportunidades, riesgos, datos, plan de 7/30 días y siguiente paso.
8. El sistema guarda leads, conversación, outcome, feedback y métricas en CRM.
9. El CRM permite operar la beta y revisar conversión del embudo.
10. El despliegue en VPS está preparado con servicio, proxy HTTPS, variables y smoke test.
11. El sistema está verificado con pruebas reales suficientes para no depender de "parece que funciona".
12. La experiencia visual pública no muestra términos internos ni sensación de cuestionario rígido.

## Checklist prompt-to-artifact

| Requisito explícito | Evidencia actual | Verificación | Estado |
|---|---|---|---|
| "Ontora-lite" para pymes españolas | `Agente_Real_CRM.html`, `app_server.py`, `Sistema_Completo.md` | Copy y prompts orientados a pymes, autónomos y personas no técnicas | Parcial: falta beta externa |
| Agente de discovery adaptativo | `AGENT_INSTRUCTIONS` y `call_codex_cli()` en `app_server.py` | Prueba real con caso newsletter/email en `AI_PROVIDER=codex`: siguió el caso y cerró en 4 turnos | Hecho local |
| Antibloqueo conversacional | `repair_repetitive_reply()` en `app_server.py` | Si la IA repite una petición de ejemplo o el usuario se frustra, el backend reconoce el atasco y avanza a impacto, herramientas, riesgo o cierre; `test_agent_quality_guard.py` lo valida | Hecho base |
| Cierre eficiente de discovery | `enforce_readiness_window()` en `app_server.py` | Con 4 turnos, foco, candidatos y confianza alta, activa informe aunque queden detalles finos; `test_discovery_flow.py` exige `ready_for_report` en clínica, inmobiliaria y consultor | Hecho base |
| Entrevista en lenguaje natural | UI chat en `Agente_Real_CRM.html` | Navegador local muestra inicio conversacional y typewriter | Hecho |
| Entiende procesos reales | Campos `facts`, `signals`, `candidate_processes`, `current_focus` | Test de clínica, inmobiliaria, consultor B2B; prueba real de email | Hecho local |
| Progreso e insights vivos | Sidebar "Lo que estoy entendiendo" en `Agente_Real_CRM.html` | DOM verificado en navegador; `updateDiscovery()` actualiza claridad, foco, señales y gaps | Hecho |
| Informe accionable y vendible | `/api/report`, `REPORT_INSTRUCTIONS`, `normalize_report()` | Informe real generado con empleado IA, oportunidades, riesgos y plan; normalización añadida tras detectar formato irregular | Hecho local |
| Informe con decisión clara | `reportHtml()` en `Agente_Real_CRM.html` | Añade "Por qué esta va primero", prioridad inicial y flujo práctico Entrada -> Clasifica -> Prepara -> Revisión | Hecho base |
| Informe con evidencia trazable | `evidence_summary` en `REPORT_INSTRUCTIONS`, `normalize_report()`, `Agente_Real_CRM.html`, `CRM_Dashboard.html`, CSV | El informe público/PDF muestra "Señales detectadas"; CRM muestra "Señales de decisión"; export CSV incluye `evidence_summary`; `test_agent_quality_guard.py` valida fallback de evidencia | Hecho base |
| Matriz visual de priorización | `priority-map` en `Agente_Real_CRM.html` | El informe sitúa oportunidades en impacto frente a factibilidad y `test_beta_smoke.py` valida que la matriz esté presente | Hecho base |
| Informe portable para usuario | `printLatestReport()` y `printableReportHtml()` en `Agente_Real_CRM.html` | Botón "Guardar PDF" abre versión imprimible; smoke test valida que está presente | Hecho base |
| Guarda leads en CRM | SQLite `crm.sqlite3`, endpoints `/api/session`, `/api/email`, `/api/chat`, `/api/report`, `/api/feedback`, `/api/leads`, `/api/lead` | `test_discovery_flow.py` crea leads y reportes; dashboard lee datos | Hecho |
| CRM con métricas de beta | `/api/metrics`, `CRM_Dashboard.html` | `curl /api/metrics` devuelve leads, inicio, email, informe, feedback y turnos | Hecho |
| Atribución de funnel | `collectAttribution()` en `Agente_Real_CRM.html`, `/api/session`, CRM, métricas y CSV | `test_beta_smoke.py` valida UTM de sesión, disponibilidad en CRM, agregación en métricas y columnas CSV | Hecho base |
| Inteligencia comercial interna | `sales_intelligence` en informe, `CRM_Dashboard.html`, CSV | CRM muestra frases útiles, objeciones e ideas de contenido; CSV exporta objeciones e ideas sin exponerlo en UI pública | Hecho base |
| CRM operable manualmente | `/api/lead/update`, controles de "Operación interna" en `CRM_Dashboard.html` | Permite cambiar estado, oferta y notas internas desde el detalle del lead; `test_beta_smoke.py` valida edición con y sin auth | Hecho base |
| CRM filtrable para operar beta | `offerFilter`, `statusFilter`, `sourceFilter` en `CRM_Dashboard.html` | Permite filtrar leads por oferta, estado y origen; smoke test valida presencia de filtros | Hecho base |
| Integración CRM externa opcional | `CRM_WEBHOOK_URL`, `CRM_WEBHOOK_SECRET`, `send_crm_webhook()` en `app_server.py`, `preflight_vps.py` | Envía email capturado, informe generado, interés CTA y feedback a Make/n8n/Zapier/Airtable/HubSpot si se configura; `test_server_guards.py` valida payload, cabecera secreta y chequeos de webhook en preflight; dashboard muestra errores de webhook | Hecho base |
| Reintento/sincronización CRM externa | `sync_crm_webhook.py`, `test_crm_webhook_sync.py`, `README.md`, `DEPLOYMENT_VPS.md` | Permite reenviar snapshots de leads existentes a un webhook externo si el CRM se configura tarde o hay que reintentar; puede omitir transcript con `--no-transcript`; release check ejecuta una prueba con receptor local y recibo en eventos | Hecho base |
| Borrado de datos de lead | `/api/lead/delete`, botón `Borrar lead` en `CRM_Dashboard.html`, nota en `PRIVACY_BETA.md` | Elimina lead y eventos asociados; `test_beta_smoke.py` valida borrado y 404 posterior | Hecho base |
| Protección CRM | `_require_admin()` protege dashboard, leads, lead, metrics, export, edición de lead y `/crm` legacy | Prueba con `ADMIN_PASSWORD`: endpoints internos devuelven `401` sin auth y `200` con auth | Hecho para VPS |
| Bloqueo de contraseña admin de ejemplo | `admin_auth_misconfigured()` en `app_server.py`, `test_server_guards.py` | Si `ADMIN_PASSWORD=change-me`, rutas admin devuelven error de configuración en vez de aceptar una contraseña conocida | Hecho base |
| Bloqueo de CRM sin contraseña en dominio público | `_require_admin()`, `local_host_header()`, `test_server_guards.py` | CRM sin `ADMIN_PASSWORD` solo se permite en `localhost`, `127.0.0.1` o `::1`; un dominio/IP pública recibe error de configuración | Hecho base |
| Exportación operativa | `/api/export.csv`, botón "Exportar CSV" en `CRM_Dashboard.html` | CSV probado localmente; `test_beta_smoke.py` comprueba protección y respuesta | Hecho |
| Backups de beta | `backup_crm.py`, `deploy/primer-empleado-ia-backup.service`, `deploy/primer-empleado-ia-backup.timer`, `test_backup_crm.py`, `backups/` ignorado por Git | Script genera copia SQLite consistente y JSONL si existe; timer diario preparado para VPS; release check prueba backup en entorno temporal | Hecho base |
| Privacidad beta | `PRIVACY_BETA.html`, `PRIVACY_BETA.md`, enlace en UI, texto corto en email-gate, `release_check.py` | Página pública HTML informa sin pedir email al inicio e incluye proveedores de CRM/webhook; documento operativo mantiene pendientes legales reales; `--public-beta` falla si MD o HTML conservan placeholders/notas públicas de beta | Parcial |
| Generación de privacidad final | `privacy_config.example.json`, `render_privacy.py`, `.gitignore`, `test_privacy_renderer.py`, `release_check.py` | Permite generar `PRIVACY_BETA.md` y `PRIVACY_BETA.html` desde datos reales; falla si conserva placeholders; `privacy_config.json` queda ignorado para no subir datos legales; release check ejecuta el test dedicado | Hecho base |
| Consentimiento al email-gate | `finalConsent` en `Agente_Real_CRM.html`, `/api/email` en `app_server.py`, `CRM_Dashboard.html`, CSV | El informe exige consentimiento explícito antes de guardar email; CRM muestra `facts.consent`; CSV exporta consentimiento; `test_beta_smoke.py` valida rechazo sin consentimiento y guardado/export | Hecho base |
| Métricas de consentimiento | `/api/metrics`, `CRM_Dashboard.html`, `test_beta_smoke.py` | Dashboard muestra tasa y número de consentimientos aceptados; smoke test valida agregación | Hecho base |
| Gate backend de informe | `/api/report` en `app_server.py` | Aunque alguien invoque la API directamente, el informe no se genera sin email válido y consentimiento; `test_beta_smoke.py` lo valida | Hecho base |
| Captura de intención comercial | Botón de siguiente paso en `Agente_Real_CRM.html`, `/api/cta`, `CRM_Dashboard.html`, CSV | El usuario puede marcar interés en el CTA recomendado; requiere email/consentimiento; CRM y CSV muestran `cta_interest`; smoke test valida guardado y exportación | Hecho base |
| Métricas de intención comercial | `/api/metrics`, `CRM_Dashboard.html` | Dashboard muestra tasa de interés CTA y CTA top; smoke test valida agregación por segmento | Hecho base |
| Métricas de calidad de beta | `/api/metrics`, `CRM_Dashboard.html`, `test_beta_smoke.py` | Dashboard muestra utilidad media del feedback y patrón principal de lo que faltó; smoke test valida `avg_feedback_rating` y `top_feedback_missing` | Hecho base |
| Salud operativa de IA/webhook | `/api/metrics`, `CRM_Dashboard.html`, eventos `ai_error`, `ai_busy`, `webhook_error` | Dashboard muestra "Salud IA", estado de webhook e incidencias recientes con detalle para detectar fallos de Codex/API/sincronización durante la beta; smoke test valida presencia | Hecho base |
| Latencia IA visible en CRM | Eventos `chat_turn` y `report_generated` en `app_server.py`, `/api/metrics`, `CRM_Dashboard.html`, `test_beta_smoke.py` | Cada respuesta/informe guarda `elapsed_seconds` y proveedor; dashboard muestra latencia media de chat e informe para decidir si Codex CLI aguanta beta o hay que migrar | Hecho base |
| Guardas antiabuso básicos | `MAX_PUBLIC_EVENTS_PER_HOUR`, `rate_limited()`, `client_ip()`, `MAX_BODY_BYTES`, `test_server_guards.py` | POST públicos tienen rate limit por IP y tamaño máximo de payload; `X-Forwarded-For` solo se respeta cuando la petición viene del proxy local; release check ejecuta prueba de rate limit, cabecera proxy y emails inválidos | Hecho base |
| Listo para beta pública en VPS | `DEPLOYMENT_VPS.md`, `VPS_LAUNCH_PACKET.md`, `deploy/install_vps.sh`, `deploy/verify_vps.sh`, `deploy/primer-empleado-ia.service`, `deploy/Caddyfile.example`, `.env.example`, `preflight_vps.py`, `test_beta_smoke.py` | Preflight, release check, instalador no-root, verificador VPS y smoke test locales OK; checklist operativo preparado; despliegue real no ejecutado | Parcial |
| Gate de release para VPS | `release_check.py`, `deploy/verify_vps.sh`, `test_public_beta_gate.py` | Agrupa sintaxis, copy público, privacidad beta, test del generador de privacidad, preflight y smoke test contra URL local/dominio; `--public-beta` exige HTTPS, no localhost, credenciales CRM, privacidad final y Codex live; test unitario valida bloqueos principales | Hecho base |
| Gate opcional de experiencia real | `release_check.py --with-browser --with-transcription`, `test_public_ui_flow.py`, `test_public_report_flow.py`, `test_transcription_local.py` | Permite sumar pruebas de navegador, cierre de informe y audio real al release check contra una URL arrancada; falla si se piden sin `--base` | Hecho base |
| Go/no-go operativo | `launch_go_no_go.py`, `test_launch_go_no_go.py`, `PRODUCTION_READINESS.md`, `VPS_LAUNCH_PACKET.md` | Ejecuta `release_check.py` y añade bloqueos explícitos de HTTPS, localhost, CRM, privacidad, prueba manual, revisión CRM y micro antes de abrir beta pública; permite `--mic-optional` si la primera beta se lanza por texto | Hecho base |
| Codex verificado como usuario systemd | `preflight_vps.py`, `deploy/install_vps.sh`, `deploy/verify_vps.sh`, `test_server_guards.py`, docs VPS | El preflight puede recibir `--service-user primeria`; si se usa `--check-codex-live`, ejecuta Codex como ese usuario, evitando el falso positivo de login como `root` | Hecho base |
| Preparación de producción | `PRODUCTION_READINESS.md` | Lista datos necesarios, variables `.env`, gate final, prueba manual obligatoria y criterios de no apertura | Hecho base |
| Plan de beta externa | `BETA_TEST_PLAN.md` | Define muestra mínima, mensaje para testers, variables a observar en CRM, criterios de éxito y experimentos por canal | Hecho base |
| Repositorio enseñable | GitHub `ptapias/encuentra-tu-primer-empleado-ia` | About actualizado con descripción de producto "Ontora-lite para pymes..." y topics `ai-discovery`, `business-automation`, `lead-magnet`, `no-code`, `pymes`, `spanish-saas` | Hecho base |
| Lista blanca de estáticos públicos | `PUBLIC_STATIC_FILES`, `ADMIN_STATIC_FILES`, `allowed_static_path()` en `app_server.py`, `test_beta_smoke.py` | Solo sirve página pública, privacidad HTML y dashboard con auth; bloquea docs, prototipos, scripts, backups y datos internos | Hecho base |
| Noindex de beta | `BETA_NOINDEX`, `/robots.txt`, `X-Robots-Tag` en `app_server.py` | Smoke test valida robots y cabecera noindex cuando la beta lo tiene activo | Hecho base |
| Dominio raíz usable | `GET /` y `HEAD /` en `app_server.py`, `test_beta_smoke.py` | Redirige a `/Agente_Real_CRM.html`; smoke test valida `HEAD /` para checks externos | Hecho base |
| UTMs conservadas desde raíz | `diagnostic_location()` en `app_server.py`, `test_beta_smoke.py` | `GET /?utm_source=...` redirige a `/Agente_Real_CRM.html?...` sin perder parámetros de atribución | Hecho base |
| Config VPS segura por defecto | `.env.example`, `preflight_vps.py`, `DEPLOYMENT_VPS.md` | Ejemplo usa `HOST=127.0.0.1` detrás de Caddy; preflight avisa si se expone `0.0.0.0` | Hecho base |
| HTTPS preparado para micrófono | `deploy/Caddyfile.example`, `release_check.py` | Caddy incluye `Permissions-Policy` con `microphone=(self)` para que la beta HTTPS pueda pedir permiso de micro en el propio dominio | Hecho base |
| Instalación VPS guiada | `deploy/install_vps.sh`, `deploy/verify_vps.sh`, `release_check.py`, `DEPLOYMENT_VPS.md` | Script crea `.env` si falta, exige contraseña real, instala systemd/backup, valida Codex como service user, valida Caddy si hay dominio y corre smoke test local; verificador ejecuta preflight, smoke local, smoke HTTPS y release gate | Hecho base |
| Verificación VPS ampliable | `deploy/verify_vps.sh`, `release_check.py --with-browser --with-transcription` | El verificador acepta `BROWSER_CHECKS=true` y `TRANSCRIPTION_CHECK=true` para sumar pruebas Playwright y audio real al release gate del dominio HTTPS si el VPS tiene dependencias disponibles | Hecho base |
| Experiencia visual comparable a startup YC | `Agente_Real_CRM.html` con hero fuerte, layout, progreso, tarjetas de proceso | Revisión visual local en escritorio y móvil: hero claro, estado inicial no técnico, compositor oculto hasta empezar, botón inicial no duplicado tras iniciar; estándar "YC-level" sigue necesitando test con usuarios | Parcial |
| Sin preguntas predefinidas | Prompt prohíbe guion fijo; Codex real adapta | Fallback sigue siendo heurístico y se usa solo para pruebas; Codex real verificado en una sesión | Parcial: faltan más casos reales |
| Sin degradación silenciosa a fallback | `ALLOW_AI_FALLBACK=false`, errores `502` e evento `ai_error` cuando falla el proveedor real | Preflight exige fallback desactivado para beta pública | Hecho |
| Control de concurrencia IA | `MAX_AI_CONCURRENCY`, `AI_QUEUE_WAIT_SECONDS`, `AiBusyError` en `app_server.py`, `test_ai_concurrency.py` | Limita procesos Codex/OpenAI concurrentes y devuelve `429` con reintento si el agente está ocupado | Hecho base |
| Espera honesta ante respuestas lentas | `startWaitStatus()` en `Agente_Real_CRM.html`, `test_beta_smoke.py` | La UI muestra contador y mensajes progresivos mientras Codex piensa o genera informe, reduciendo sensación de bloqueo en esperas largas | Hecho base |
| Sin UI mediocre ni términos internos | Búsqueda pública eliminó JSON, fallback, CRM, "informe potente" | `test_beta_smoke.py` comprueba gancho y ausencia de textos internos básicos | Hecho base |
| Micrófono | `MediaRecorder`, `/transcribe`, `WHISPER_BIN`, `FFMPEG_BIN`, `/api/capabilities` | Smoke test cubre disponibilidad del servicio; permisos/grabación real siguen siendo prueba manual | Parcial |
| Transcripción con audio real | `test_transcription_local.py`, `/transcribe`, Whisper local | Prueba opcional genera audio con `say`, lo convierte con `ffmpeg`, lo envía a `/transcribe` y exige texto no vacío; no sustituye permisos reales de navegador | Hecho local |
| Feedback al final | UI de informe con rating, campos de claridad/faltantes/mejora y `/api/feedback` | Requiere email/consentimiento; `test_beta_smoke.py` valida guardado estructurado en CRM; dashboard y CSV muestran campos de feedback | Hecho |
| Email-gate honesto | `Agente_Real_CRM.html`, `README.md`, `test_beta_smoke.py` | CTA dice "Generar informe" y no promete envío por correo mientras no haya proveedor conectado | Hecho base |
| Cierre visual completo | `test_public_report_flow.py`, `Agente_Real_CRM.html` | Prueba de navegador con respuestas simuladas valida cierre del agente, botón `Generar informe`, email-gate final con consentimiento, render del informe, matriz, feedback y guardado de feedback | Hecho base |
| Recuperación ante recarga | `localStorage` en `Agente_Real_CRM.html`, `test_session_restore_flow.py` conserva `lead_id`, conversación, email y estado de discovery | Prueba de navegador recupera sesión a mitad de discovery con input/micro activos, y sesión lista para informe con botón `Generar informe` visible | Hecho base |

## Evidencia de comandos recientes

```bash
python3 -m py_compile app_server.py test_discovery_flow.py test_beta_smoke.py
python3 test_agent_quality_guard.py
python3 test_server_guards.py
python3 test_privacy_renderer.py
python3 test_public_ui_flow.py --base http://localhost:8787
python3 test_public_report_flow.py --base http://localhost:8787
python3 test_transcription_local.py --base http://localhost:8787
python3 test_crm_webhook_sync.py
python3 test_beta_smoke.py --base http://localhost:8787
python3 test_beta_smoke.py --base http://localhost:8788 --admin-user admin --admin-password testpass
python3 release_check.py --env /tmp/primer-empleado-valid.env --base http://localhost:8787
python3 release_check.py --env /tmp/primer-empleado-valid.env --base http://localhost:8787 --with-browser --with-transcription
python3 test_launch_go_no_go.py
python3 test_public_beta_gate.py
python3 launch_go_no_go.py --env /tmp/primer-empleado-valid.env --base http://localhost:8787 --with-browser --with-transcription --manual-production-tested --crm-reviewed --mic-tested
python3 release_check.py --env /tmp/primer-empleado-valid.env --service-user "$(whoami)" --base http://localhost:8787
APP_DIR="$PWD" CHECK_CODEX_LIVE=false ./deploy/verify_vps.sh
curl http://localhost:8787/healthz
curl http://localhost:8787/api/metrics
curl -X POST http://localhost:8787/api/lead/update
```

Resultado reciente:

- `healthz`: expone `ok`, `provider`, `transcription`, `ai_concurrency`, `beta_noindex` y `version`; último valor local verificado: `457e7ae`.
- Smoke test local: OK, incluyendo actualización de lead y feedback estructurado.
- Smoke test con `ADMIN_PASSWORD`: OK en `1761140` con instancia temporal en `localhost:8791`; `/api/lead/update`, `/api/lead/delete`, `/crm`, `/api/metrics` y `/api/export.csv` devuelven `401` sin auth y `200` con auth; `/api/feedback` guarda datos estructurados y el CRM los devuelve con autenticación.
- Release check local: OK con `.env` temporal válido y URL local; privacidad beta queda como warning mientras no se completen datos legales.
- Preflight valida `MAX_AI_CONCURRENCY` y `AI_QUEUE_WAIT_SECONDS`; `healthz` expone `ai_concurrency`; `test_ai_concurrency.py` prueba el error de agente ocupado.
- Smoke test valida que `HEAD /` redirige al diagnóstico para que checks externos no vean un falso 404.
- El informe normalizado incluye `evidence_summary` aunque el modelo no lo devuelva explícitamente; lo deriva de frases útiles o facts como frecuencia, impacto, herramienta y riesgo.
- `.env.example` usa `HOST=127.0.0.1`; `preflight_vps.py` avisa si la app queda expuesta públicamente sin pasar por Caddy.
- Métricas locales: el CRM registra leads, conversaciones iniciadas, emails, informes y feedback; el CSV exporta rating, claridad, faltantes y mejora sugerida.
- Atribución de funnel: `utm_source`, `utm_medium`, `utm_campaign`, `video` y `ref` se guardan en `facts.attribution`; el dashboard muestra origen/campaña y el CSV exporta source/medium/campaign/video/ref.
- Inteligencia comercial: el informe normalizado puede incluir frases útiles, objeciones e ideas de contenido; el CRM y CSV lo muestran para ventas/newsletter/YouTube.
- Actualización manual de CRM: endpoint protegido y edición estado/oferta/notas desde dashboard añadidos.
- Prueba real de discovery con Codex en clínica dental, inmobiliaria y consultor B2B: OK en `457e7ae`; los tres casos cerraron `ready_for_report=true`, generaron 3 oportunidades, no usaron fallback y recomendaron empleados IA específicos por sector. Latencias: clínica dental 133.9s, inmobiliaria 123.1s, consultor B2B 118.8s.
- Revisión visual con Chrome: hero mantiene el gancho "¿Dónde se te escapa tiempo, dinero o clientes?", informe muestra matriz de decisión y flujo práctico, sin términos internos como JSON/fallback/descargar. En móvil, el compositor queda oculto hasta empezar y aparece activo al iniciar la sesión.
- Preflight local: falla correctamente con `.env.example` y pasa con un `.env` temporal válido.
- Preflight con `--check-codex-live`: Codex CLI responde correctamente en local.
- Preflight con `--service-user`: valida que el usuario exista; con `--check-codex-live` exige ejecutarse como root/sudo para probar Codex como el usuario systemd.
- `deploy/verify_vps.sh`: probado en modo local con CRM protegido; valida preflight, smoke local y deja preparado el camino para smoke HTTPS/dominio.
- `test_privacy_renderer.py`: valida que la privacidad con placeholders falle y que una configuración final genere MD/HTML sin marcadores de beta.
- UI de espera lenta: prueba con navegador simulando `/api/chat` confirma que se muestra estado progresivo y vuelve al progreso normal cuando llega la respuesta.
- Prueba UI pública reusable: `test_public_ui_flow.py` valida escritorio, móvil, arranque sin email y estado de espera del agente.
- Prueba de cierre público reusable: `test_public_report_flow.py` valida que el usuario solo deja email al final y que el informe/feedback aparecen correctamente.
- Prueba de transcripción real: `test_transcription_local.py` valida audio generado localmente contra `/transcribe`; la prueba puede saltarse si faltan `say`, `ffmpeg` o Whisper.
- Prueba de sincronización CRM: `test_crm_webhook_sync.py` crea una base temporal, levanta un receptor webhook local, envía un snapshot y comprueba cabeceras, payload y recibo `crm_webhook_snapshot_synced`.
- Go/no-go local/controlado: `launch_go_no_go.py` devuelve `GO` contra `localhost` cuando el release ampliado pasa y las confirmaciones manuales simuladas están presentes; con credenciales pasadas contra una instancia sin auth devuelve `NO_GO`, detectando una configuración que no sirve para producción.
- Prueba anti-fallback silencioso: con `CODEX_BIN` inválido y `ALLOW_AI_FALLBACK=false`, `/api/chat` devuelve `502` y no genera respuesta fallback.

## Huecos no cerrados

| Hueco | Por qué importa | Próxima acción |
|---|---|---|
| VPS no desplegado todavía | "Listo para beta pública" requiere comprobar dominio, HTTPS, systemd, auth y persistencia en servidor real | Ejecutar `DEPLOYMENT_VPS.md` y luego `DOMAIN=... ./deploy/verify_vps.sh` en el VPS |
| Faltan datos de lanzamiento | Sin dominio, acceso SSH, contraseña CRM y datos legales no se puede completar `--public-beta` | Recoger los datos de `VPS_LAUNCH_PACKET.md` y generar privacidad con `render_privacy.py` |
| Codex CLI en producción es frágil para tráfico abierto | Puede tardar, romper sesión o no estar pensado como backend multiusuario | Beta privada primero; si hay uso real, migrar a API oficial o cola supervisada |
| Grabación real de micrófono no cubierta por smoke test | Los permisos del navegador requieren prueba manual aunque `/api/capabilities` valide binarios | Probar micrófono manualmente en local y en VPS con HTTPS |
| Visual "startup YC" no validado con usuarios externos | Puede verse bien para nosotros pero no convertir | Test con 5 usuarios: claridad del hero, ganas de empezar, comprensión del informe |
| Calidad adaptativa probada en pocos casos reales con Codex | Un caso bueno no garantiza robustez en sectores distintos | Ejecutar 5 discovery sessions reales: newsletter, clínica, inmobiliaria, agencia, ecommerce |
| CRM externo real no elegido | El webhook ya permite sincronizar con Make/n8n/Zapier/Airtable/HubSpot, pero falta escoger destino y configurar credenciales reales | Elegir CRM/destino y completar `CRM_WEBHOOK_URL` en VPS |
| Privacidad pendiente de datos reales | La beta ya informa, pero falta responsable legal, contacto y plazo concreto | Rellenar `privacy_config.json`, ejecutar `render_privacy.py` y correr `release_check.py --public-beta` |

## Decisión de auditoría

No se puede marcar el objetivo como completo todavía.

El MVP local está en estado fuerte para pruebas internas y demo controlada. La pieza que falta para cumplir literalmente "beta pública en VPS" es ejecutar despliegue real, activar autenticación, correr el smoke test contra el dominio y hacer 3-5 pruebas externas.
