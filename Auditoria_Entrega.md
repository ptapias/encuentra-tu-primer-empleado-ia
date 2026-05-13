# Auditoría de entrega actual

Objetivo auditado: construir una versión "Ontora-lite" para pymes españolas de "Encuentra Tu Primer Empleado IA": discovery conversacional, agente adaptativo, informe accionable, CRM interno y base lista para beta pública.

## Estado actual

| Área | Estado | Evidencia |
|---|---:|---|
| Pantalla inicial | Hecho | `Agente_Real_CRM.html`: gancho "¿Dónde se te escapa tiempo, dinero o clientes?", inicio sin formulario previo, CTA "Analizar mi negocio" |
| Conversación natural | Hecho en modo real | `app_server.py`: proveedor `AI_PROVIDER=codex` con prompt adaptativo; evita guion fijo y optimiza para 7-10 minutos |
| Modo local de prueba | Hecho | `AI_PROVIDER=fallback` permite probar flujo, CRM, informe y UI sin consumir API |
| Micrófono y transcripción | Hecho local | `/transcribe` con Whisper local; UI con estados de grabación y transcripción |
| Progreso e insights vivos | Hecho | Sidebar "Lo que estoy entendiendo", foco actual, claridad, señales y gaps |
| Email al final | Hecho | `/api/session` permite empezar sin email; `/api/email` lo captura solo antes del informe |
| Informe | Hecho | `/api/report` genera recomendación, oportunidades, riesgos, plan de 7 y 30 días y CTA |
| Feedback | Hecho | `/api/feedback` guarda feedback asociado al lead |
| CRM interno | Hecho | `CRM_Dashboard.html`, SQLite `crm.sqlite3`, endpoints `/api/leads`, `/api/lead` y `/api/metrics` |
| Métricas de beta | Hecho | Dashboard con leads, inicio de conversación, captura de email, informes, feedback y media de turnos |
| Validación automatizada | Hecho | `test_discovery_flow.py` prueba clínica dental, inmobiliaria y consultor B2B |
| VPS | Preparado, no desplegado | `DEPLOYMENT_VPS.md`, `deploy/primer-empleado-ia.service`, `deploy/Caddyfile.example` |
| GitHub | Hecho | Repositorio `ptapias/encuentra-tu-primer-empleado-ia` ya existe y tiene historial de commits |

## Pruebas realizadas en esta revisión

- Compilación Python: `app_server.py` y `test_discovery_flow.py` sin errores.
- Validación JavaScript: script de `Agente_Real_CRM.html` sin errores de sintaxis.
- Test funcional local en `AI_PROVIDER=fallback`: 3 casos pasan y generan informe.
- Revisión en navegador interno: la pantalla inicial muestra el gancho correcto y no enseña términos internos como JSON, CRM, fallback o "informe potente".
- Endpoint `/api/metrics`: devuelve métricas de embudo y está protegido junto al CRM cuando `ADMIN_PASSWORD` está configurado.
- Prueba de protección CRM: `/api/metrics` devuelve `401` sin auth y `200` con auth básica cuando `ADMIN_PASSWORD` está activo.

## Lo que ya no debe volver

- Preguntas fijas disfrazadas de chat.
- Pedir email antes de que el usuario haya recibido valor.
- Botones o textos públicos como "descargar JSON", "CRM", "fallback" o "informe potente".
- Repetir la misma pregunta cuando el usuario ya dio una señal útil.
- Alargar la entrevista por perfeccionismo cuando ya hay criterio suficiente.

## Riesgos pendientes antes de beta pública

| Riesgo | Impacto | Mitigación recomendada |
|---|---|---|
| Usar Codex como motor en producción puede ser frágil | Alto | Para beta interna, probar `AI_PROVIDER=codex`; para beta pública seria, decidir si se acepta API oficial o cola semi-manual |
| El fallback no representa la calidad real del agente | Medio | Usarlo solo para pruebas de flujo; validar casos reales con `AI_PROVIDER=codex` |
| Transcripción local depende de Whisper/ffmpeg instalados | Medio | Validar en VPS o cambiar a transcripción vía navegador/API |
| No hay autenticación fuerte en CRM si no se configuran variables | Alto | En VPS configurar `ADMIN_PASSWORD`, HTTPS y firewall |
| No hay analítica de embudo completa | Medio | Añadir métricas de start, turnos, ready, email, informe y feedback |

## Siguiente hito recomendado

1. Probar 3 sesiones reales con `AI_PROVIDER=codex`.
2. Ajustar prompt con los fallos reales de esas conversaciones.
3. Activar autenticación del CRM.
4. Subir a VPS como beta privada.
5. Enviar a 10-20 usuarios de confianza y recoger feedback cualitativo.
