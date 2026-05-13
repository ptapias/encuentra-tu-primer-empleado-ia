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
| Matriz visual de priorización | `priority-map` en `Agente_Real_CRM.html` | El informe sitúa oportunidades en impacto frente a factibilidad y `test_beta_smoke.py` valida que la matriz esté presente | Hecho base |
| Informe portable para usuario | `printLatestReport()` y `printableReportHtml()` en `Agente_Real_CRM.html` | Botón "Guardar PDF" abre versión imprimible; smoke test valida que está presente | Hecho base |
| Guarda leads en CRM | SQLite `crm.sqlite3`, endpoints `/api/session`, `/api/email`, `/api/chat`, `/api/report`, `/api/feedback`, `/api/leads`, `/api/lead` | `test_discovery_flow.py` crea leads y reportes; dashboard lee datos | Hecho |
| CRM con métricas de beta | `/api/metrics`, `CRM_Dashboard.html` | `curl /api/metrics` devuelve leads, inicio, email, informe, feedback y turnos | Hecho |
| Atribución de funnel | `collectAttribution()` en `Agente_Real_CRM.html`, `/api/session`, CRM, métricas y CSV | `test_beta_smoke.py` valida UTM de sesión, disponibilidad en CRM, agregación en métricas y columnas CSV | Hecho base |
| Inteligencia comercial interna | `sales_intelligence` en informe, `CRM_Dashboard.html`, CSV | CRM muestra frases útiles, objeciones e ideas de contenido; CSV exporta objeciones e ideas sin exponerlo en UI pública | Hecho base |
| CRM operable manualmente | `/api/lead/update`, controles de "Operación interna" en `CRM_Dashboard.html` | Permite cambiar estado, oferta y notas internas desde el detalle del lead; `test_beta_smoke.py` valida edición con y sin auth | Hecho base |
| CRM filtrable para operar beta | `offerFilter`, `statusFilter`, `sourceFilter` en `CRM_Dashboard.html` | Permite filtrar leads por oferta, estado y origen; smoke test valida presencia de filtros | Hecho base |
| Borrado de datos de lead | `/api/lead/delete`, botón `Borrar lead` en `CRM_Dashboard.html`, nota en `PRIVACY_BETA.md` | Elimina lead y eventos asociados; `test_beta_smoke.py` valida borrado y 404 posterior | Hecho base |
| Protección CRM | `_require_admin()` protege dashboard, leads, lead, metrics, export, edición de lead y `/crm` legacy | Prueba con `ADMIN_PASSWORD`: endpoints internos devuelven `401` sin auth y `200` con auth | Hecho para VPS |
| Exportación operativa | `/api/export.csv`, botón "Exportar CSV" en `CRM_Dashboard.html` | CSV probado localmente; `test_beta_smoke.py` comprueba protección y respuesta | Hecho |
| Backups de beta | `backup_crm.py`, `deploy/primer-empleado-ia-backup.service`, `deploy/primer-empleado-ia-backup.timer`, `backups/` ignorado por Git | Script genera copia SQLite consistente y JSONL si existe; timer diario preparado para VPS | Hecho base |
| Privacidad beta | `PRIVACY_BETA.html`, `PRIVACY_BETA.md`, enlace en UI, texto corto en email-gate | Página pública HTML sin placeholders internos; documento operativo mantiene pendientes legales reales | Parcial |
| Listo para beta pública en VPS | `DEPLOYMENT_VPS.md`, `deploy/install_vps.sh`, `deploy/primer-empleado-ia.service`, `deploy/Caddyfile.example`, `.env.example`, `preflight_vps.py`, `test_beta_smoke.py` | Preflight, release check, instalador no-root y smoke test locales OK; despliegue real no ejecutado | Parcial |
| Gate de release para VPS | `release_check.py` | Agrupa sintaxis, copy público, privacidad beta, preflight y smoke test contra URL local/dominio; `--public-beta` exige HTTPS, no localhost, credenciales CRM, privacidad final y Codex live | Hecho base |
| Plan de beta externa | `BETA_TEST_PLAN.md` | Define muestra mínima, mensaje para testers, variables a observar en CRM, criterios de éxito y experimentos por canal | Hecho base |
| Lista blanca de estáticos públicos | `PUBLIC_STATIC_FILES`, `ADMIN_STATIC_FILES`, `allowed_static_path()` en `app_server.py`, `test_beta_smoke.py` | Solo sirve página pública, privacidad HTML y dashboard con auth; bloquea docs, prototipos, scripts, backups y datos internos | Hecho base |
| Noindex de beta | `BETA_NOINDEX`, `/robots.txt`, `X-Robots-Tag` en `app_server.py` | Smoke test valida robots y cabecera noindex cuando la beta lo tiene activo | Hecho base |
| Dominio raíz usable | `GET /` y `HEAD /` en `app_server.py`, `test_beta_smoke.py` | Redirige a `/Agente_Real_CRM.html`; smoke test valida `HEAD /` para checks externos | Hecho base |
| UTMs conservadas desde raíz | `diagnostic_location()` en `app_server.py`, `test_beta_smoke.py` | `GET /?utm_source=...` redirige a `/Agente_Real_CRM.html?...` sin perder parámetros de atribución | Hecho base |
| Config VPS segura por defecto | `.env.example`, `preflight_vps.py`, `DEPLOYMENT_VPS.md` | Ejemplo usa `HOST=127.0.0.1` detrás de Caddy; preflight avisa si se expone `0.0.0.0` | Hecho base |
| Instalación VPS guiada | `deploy/install_vps.sh`, `release_check.py`, `DEPLOYMENT_VPS.md` | Script crea `.env` si falta, exige contraseña real, instala systemd/backup, valida Caddy si hay dominio y corre smoke test local; release check valida que exista y sea ejecutable | Hecho base |
| Experiencia visual comparable a startup YC | `Agente_Real_CRM.html` con hero fuerte, layout, progreso, tarjetas de proceso | Revisión visual local hecha; estándar "YC-level" es subjetivo y falta test con usuarios | Parcial |
| Sin preguntas predefinidas | Prompt prohíbe guion fijo; Codex real adapta | Fallback sigue siendo heurístico y se usa solo para pruebas; Codex real verificado en una sesión | Parcial: faltan más casos reales |
| Sin degradación silenciosa a fallback | `ALLOW_AI_FALLBACK=false`, errores `502` e evento `ai_error` cuando falla el proveedor real | Preflight exige fallback desactivado para beta pública | Hecho |
| Control de concurrencia IA | `MAX_AI_CONCURRENCY`, `AI_QUEUE_WAIT_SECONDS`, `AiBusyError` en `app_server.py`, `test_ai_concurrency.py` | Limita procesos Codex/OpenAI concurrentes y devuelve `429` con reintento si el agente está ocupado | Hecho base |
| Sin UI mediocre ni términos internos | Búsqueda pública eliminó JSON, fallback, CRM, "informe potente" | `test_beta_smoke.py` comprueba gancho y ausencia de textos internos básicos | Hecho base |
| Micrófono | `MediaRecorder`, `/transcribe`, `WHISPER_BIN`, `FFMPEG_BIN`, `/api/capabilities` | Smoke test cubre disponibilidad del servicio; permisos/grabación real siguen siendo prueba manual | Parcial |
| Feedback al final | UI de informe con rating, campos de claridad/faltantes/mejora y `/api/feedback` | `test_beta_smoke.py` valida guardado estructurado en CRM; dashboard y CSV muestran campos de feedback | Hecho |
| Email-gate honesto | `Agente_Real_CRM.html`, `README.md`, `test_beta_smoke.py` | CTA dice "Generar informe" y no promete envío por correo mientras no haya proveedor conectado | Hecho base |
| Recuperación ante recarga | `localStorage` en `Agente_Real_CRM.html` conserva `lead_id`, conversación, email y estado de discovery | JS validado; prueba en navegador recupera conversación tras reload | Hecho base |

## Evidencia de comandos recientes

```bash
python3 -m py_compile app_server.py test_discovery_flow.py test_beta_smoke.py
python3 test_agent_quality_guard.py
python3 test_beta_smoke.py --base http://localhost:8787
python3 test_beta_smoke.py --base http://localhost:8788 --admin-user admin --admin-password testpass
python3 release_check.py --env /tmp/primer-empleado-valid.env --base http://localhost:8787
curl http://localhost:8787/healthz
curl http://localhost:8787/api/metrics
curl -X POST http://localhost:8787/api/lead/update
```

Resultado reciente:

- `healthz`: `{"ok": true, "provider": "codex"}`
- Smoke test local: OK, incluyendo actualización de lead y feedback estructurado.
- Smoke test con `ADMIN_PASSWORD`: OK; `/api/lead/update`, `/crm`, `/api/metrics` y `/api/export.csv` devuelven `401` sin auth y `200` con auth; `/api/feedback` guarda datos estructurados y el CRM los devuelve con autenticación.
- Release check local: OK con `.env` temporal válido y URL local; privacidad beta queda como warning mientras no se completen datos legales.
- Preflight valida `MAX_AI_CONCURRENCY` y `AI_QUEUE_WAIT_SECONDS`; `healthz` expone `ai_concurrency`; `test_ai_concurrency.py` prueba el error de agente ocupado.
- Smoke test valida que `HEAD /` redirige al diagnóstico para que checks externos no vean un falso 404.
- `.env.example` usa `HOST=127.0.0.1`; `preflight_vps.py` avisa si la app queda expuesta públicamente sin pasar por Caddy.
- Métricas locales: el CRM registra leads, conversaciones iniciadas, emails, informes y feedback; el CSV exporta rating, claridad, faltantes y mejora sugerida.
- Atribución de funnel: `utm_source`, `utm_medium`, `utm_campaign`, `video` y `ref` se guardan en `facts.attribution`; el dashboard muestra origen/campaña y el CSV exporta source/medium/campaign/video/ref.
- Inteligencia comercial: el informe normalizado puede incluir frases útiles, objeciones e ideas de contenido; el CRM y CSV lo muestran para ventas/newsletter/YouTube.
- Actualización manual de CRM: endpoint protegido y edición estado/oferta/notas desde dashboard añadidos.
- Prueba real de discovery con Codex en clínica dental, inmobiliaria y consultor B2B: detectó foco correcto e informes específicos; se corrigió exceso de prudencia para activar informe cuando ya hay confianza alta.
- Revisión visual con Chrome: hero mantiene el gancho "¿Dónde se te escapa tiempo, dinero o clientes?", informe muestra matriz de decisión y flujo práctico, sin términos internos como JSON/fallback/descargar.
- Preflight local: falla correctamente con `.env.example` y pasa con un `.env` temporal válido.
- Preflight con `--check-codex-live`: Codex CLI responde correctamente en local.
- Prueba anti-fallback silencioso: con `CODEX_BIN` inválido y `ALLOW_AI_FALLBACK=false`, `/api/chat` devuelve `502` y no genera respuesta fallback.

## Huecos no cerrados

| Hueco | Por qué importa | Próxima acción |
|---|---|---|
| VPS no desplegado todavía | "Listo para beta pública" requiere comprobar dominio, HTTPS, systemd, auth y persistencia en servidor real | Ejecutar `DEPLOYMENT_VPS.md` en el VPS y correr `test_beta_smoke.py` contra el dominio |
| Codex CLI en producción es frágil para tráfico abierto | Puede tardar, romper sesión o no estar pensado como backend multiusuario | Beta privada primero; si hay uso real, migrar a API oficial o cola supervisada |
| Grabación real de micrófono no cubierta por smoke test | Los permisos del navegador requieren prueba manual aunque `/api/capabilities` valide binarios | Probar micrófono manualmente en local y en VPS con HTTPS |
| Visual "startup YC" no validado con usuarios externos | Puede verse bien para nosotros pero no convertir | Test con 5 usuarios: claridad del hero, ganas de empezar, comprensión del informe |
| Calidad adaptativa probada en pocos casos reales con Codex | Un caso bueno no garantiza robustez en sectores distintos | Ejecutar 5 discovery sessions reales: newsletter, clínica, inmobiliaria, agencia, ecommerce |
| Integración directa con CRM externo no implementada | CSV ya cubre operación manual inicial, pero no sincroniza con HubSpot/Airtable/etc. | Integrar cuando haya los primeros testers y un CRM elegido |
| Privacidad pendiente de datos reales | La beta ya informa, pero falta responsable legal, contacto y plazo concreto | Completar `PRIVACY_BETA.md` antes de tráfico público abierto |

## Decisión de auditoría

No se puede marcar el objetivo como completo todavía.

El MVP local está en estado fuerte para pruebas internas y demo controlada. La pieza que falta para cumplir literalmente "beta pública en VPS" es ejecutar despliegue real, activar autenticación, correr el smoke test contra el dominio y hacer 3-5 pruebas externas.
