# MVP final: Encuentra Tu Primer Empleado IA

## Definición de "enseñable"

La versión enseñable debe permitir que una persona no técnica entre desde YouTube/newsletter, deje su email, converse con un agente, reciba un informe útil y deje feedback. Internamente, el equipo debe ver el lead en CRM con conversación, score, recomendación y siguiente paso.

## Definición de "vendible"

La versión vendible debe poder abrirse a tráfico real con límites, analítica, privacidad básica, dashboard protegido, estabilidad de despliegue y una propuesta comercial clara al final del informe.

## Estado actual

- Chat conversacional funcional.
- Proveedor `codex` vía Codex CLI para pruebas internas sin API key.
- Proveedor `openai` opcional.
- CRM SQLite con conversación, informe y feedback.
- Dashboard interno.
- Micrófono y transcripción local.
- Informe con oportunidades, riesgos, plan de 7/30 días y CTA.

## Brechas críticas

1. Despliegue en VPS con dominio y HTTPS.
2. Autenticación obligatoria del CRM.
3. Límites antiabuso y email obligatorio.
4. Copys públicos menos técnicos y más comerciales.
5. Política de privacidad básica.
6. Exportación o integración posterior con CRM externo/newsletter.
7. Pruebas de 10 casos reales antes de abrirlo.
8. Medición de conversión: visita, inicio, informe, feedback, CTA.

## Tramo 1: beta privada enseñable

- Página pública del diagnóstico sin panel de leads.
- CRM protegido con usuario/contraseña.
- Configuración `.env`.
- Servicio systemd para VPS.
- Proxy HTTPS con Caddy.
- Health check.
- Email obligatorio.
- Límite de turnos y tamaño de mensajes.

## Tramo 2: beta pública controlada

- Dominio final.
- Texto legal mínimo.
- Export CSV desde CRM.
- Campos de consentimiento.
- Eventos de funnel.
- Pantalla final con CTA personalizada.
- Informe más visual para compartir.

## Tramo 3: versión vendible

- Integración Beehiiv/ConvertKit o Airtable/HubSpot.
- Cola asíncrona para informes lentos.
- Email automático de entrega.
- Login real para admin.
- Backups automáticos.
- Métricas en dashboard.
- Experimentos por canal de YouTube.

## Criterios de salida de beta

- 30 diagnósticos completados.
- 60%+ de usuarios llegan al informe.
- 40%+ deja feedback.
- 20%+ hace clic en CTA final.
- 5+ leads cualificados para cohort o implementación.
- Menos de 10% de informes percibidos como genéricos.
