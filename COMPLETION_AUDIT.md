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
| Entrevista en lenguaje natural | UI chat en `Agente_Real_CRM.html` | Navegador local muestra inicio conversacional y typewriter | Hecho |
| Entiende procesos reales | Campos `facts`, `signals`, `candidate_processes`, `current_focus` | Test de clínica, inmobiliaria, consultor B2B; prueba real de email | Hecho local |
| Progreso e insights vivos | Sidebar "Lo que estoy entendiendo" en `Agente_Real_CRM.html` | DOM verificado en navegador; `updateDiscovery()` actualiza claridad, foco, señales y gaps | Hecho |
| Informe accionable y vendible | `/api/report`, `REPORT_INSTRUCTIONS`, `normalize_report()` | Informe real generado con empleado IA, oportunidades, riesgos y plan; normalización añadida tras detectar formato irregular | Hecho local |
| Guarda leads en CRM | SQLite `crm.sqlite3`, endpoints `/api/session`, `/api/email`, `/api/chat`, `/api/report`, `/api/feedback`, `/api/leads`, `/api/lead` | `test_discovery_flow.py` crea leads y reportes; dashboard lee datos | Hecho |
| CRM con métricas de beta | `/api/metrics`, `CRM_Dashboard.html` | `curl /api/metrics` devuelve leads, inicio, email, informe, feedback y turnos | Hecho |
| Protección CRM | `_require_admin()` protege dashboard, leads, lead y metrics | Prueba con `ADMIN_PASSWORD`: `/api/metrics` devuelve `401` sin auth y `200` con auth | Hecho para VPS |
| Exportación operativa | `/api/export.csv`, botón "Exportar CSV" en `CRM_Dashboard.html` | CSV probado localmente; `test_beta_smoke.py` comprueba protección y respuesta | Hecho |
| Backups de beta | `backup_crm.py`, `backups/` ignorado por Git | Script genera copia SQLite consistente y JSONL si existe | Hecho |
| Privacidad beta | `PRIVACY_BETA.md`, enlace en UI, texto corto en email-gate | Basado en enfoque de información por capas de AEPD; pendiente completar datos legales reales | Parcial |
| Listo para beta pública en VPS | `DEPLOYMENT_VPS.md`, `deploy/primer-empleado-ia.service`, `deploy/Caddyfile.example`, `.env.example`, `preflight_vps.py`, `test_beta_smoke.py` | Preflight y smoke test locales OK; despliegue real no ejecutado | Parcial |
| Experiencia visual comparable a startup YC | `Agente_Real_CRM.html` con hero fuerte, layout, progreso, tarjetas de proceso | Revisión visual local hecha; estándar "YC-level" es subjetivo y falta test con usuarios | Parcial |
| Sin preguntas predefinidas | Prompt prohíbe guion fijo; Codex real adapta | Fallback sigue siendo heurístico y se usa solo para pruebas; Codex real verificado en una sesión | Parcial: faltan más casos reales |
| Sin UI mediocre ni términos internos | Búsqueda pública eliminó JSON, fallback, CRM, "informe potente" | `test_beta_smoke.py` comprueba gancho y ausencia de textos internos básicos | Hecho base |
| Micrófono | `MediaRecorder`, `/transcribe`, `WHISPER_BIN`, `FFMPEG_BIN`, `/api/capabilities` | Smoke test cubre disponibilidad del servicio; permisos/grabación real siguen siendo prueba manual | Parcial |
| Feedback al final | UI de informe con textarea y `/api/feedback` | Endpoint y dashboard leen feedback; hay 1 feedback registrado en métricas | Hecho |

## Evidencia de comandos recientes

```bash
python3 -m py_compile app_server.py test_discovery_flow.py test_beta_smoke.py
python3 test_beta_smoke.py --base http://localhost:8787
curl http://localhost:8787/healthz
curl http://localhost:8787/api/metrics
```

Resultado reciente:

- `healthz`: `{"ok": true, "provider": "codex"}`
- Smoke test local: OK.
- Métricas locales: 43 leads, 41 conversaciones iniciadas, 35 emails, 30 informes, 1 feedback.
- Preflight local: falla correctamente con `.env.example` y pasa con un `.env` temporal válido.
- Preflight con `--check-codex-live`: Codex CLI responde correctamente en local.

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
