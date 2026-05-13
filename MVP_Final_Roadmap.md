# MVP final: Encuentra Tu Primer Empleado IA

## Definición de "enseñable"

La versión enseñable debe permitir que una persona no técnica entre desde YouTube/newsletter, empiece sin fricción, converse con un agente, deje su email solo cuando el diagnóstico esté listo, reciba un informe útil y deje feedback. Internamente, el equipo debe ver el lead en CRM con conversación, score, recomendación y siguiente paso.

## Posicionamiento de producto

El producto no debe sentirse como "otro chat con IA". La promesa de entrada es: "¿Dónde se te escapa tiempo, dinero o clientes?". El encuadre correcto es una discovery session ligera: un agente que analiza el negocio como lo haría un consultor, entiende procesos, repregunta con criterio y detecta qué tendría sentido automatizar primero.

## Definición de "vendible"

La versión vendible debe poder abrirse a tráfico real con límites, analítica, privacidad básica, dashboard protegido, estabilidad de despliegue y una propuesta comercial clara al final del informe.

## Estado actual

- Chat conversacional funcional.
- Proveedor `codex` vía Codex CLI para pruebas internas sin API key.
- Proveedor `openai` opcional.
- CRM SQLite con conversación, informe y feedback.
- Dashboard interno.
- Micrófono y transcripción local.
- Informe con oportunidades, matriz de priorización, riesgos, plan de 7/30 días, CTA y feedback.
- Gate de release `--public-beta` para evitar abrir sin HTTPS, CRM protegido, privacidad final y proveedor IA verificado.

## Brechas críticas

1. Despliegue en VPS con dominio y HTTPS.
2. Completar privacidad final con datos legales/contacto reales.
3. Probar micrófono en dominio HTTPS real.
4. Ejecutar 5-10 casos reales con usuarios externos.
5. Conectar email/newsletter o decidir operación manual de seguimiento.
6. Exportación o integración posterior con CRM externo/newsletter.
7. Medición de conversión: visita, inicio, informe, feedback, CTA.

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
