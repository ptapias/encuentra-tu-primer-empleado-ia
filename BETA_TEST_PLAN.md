# Plan de prueba beta

Objetivo: validar si el diagnóstico entiende negocios reales, recomienda automatizaciones útiles y genera leads cualificados sin llamada manual.

## Muestra mínima

Recluta 8-12 personas. Prioridad:

- 2 consultores/coaches/formadores.
- 2 agencias o servicios B2B.
- 2 negocios locales con WhatsApp, reservas o atención al cliente.
- 1 inmobiliaria o comercial con muchos leads.
- 1 ecommerce o negocio con soporte/email recurrente.

## Instrucción para testers

Envía este texto o usa las variantes listas de `FIRST_TESTERS_PACKET.md`:

> Estoy probando una herramienta gratuita que analiza tu negocio y te dice qué procesos podrías automatizar primero con IA. Funciona como una mini sesión de discovery: le cuentas tu caso, te repregunta y al final te genera un informe. Lo más útil es que respondas con ejemplos reales, como si estuvieras hablando conmigo. Al terminar, deja feedback sincero sobre qué te sirvió y qué echaste en falta.

No les expliques el sistema por dentro. Queremos medir si la promesa se entiende sola.

## Qué observar

Para cada tester, revisa en el CRM:

- Sector y tipo de negocio.
- Origen del lead.
- Número de turnos hasta `ready_for_report`.
- Si dejó email.
- Si generó informe.
- Empleado IA recomendado.
- Oferta recomendada.
- Rating de feedback.
- Qué echó en falta.
- Frases literales útiles para copy o YouTube.

## Preguntas de seguimiento

Si puedes escribirles después, usa estas 5:

1. ¿Sentiste que el agente entendió tu negocio?
2. ¿La recomendación fue concreta o genérica?
3. ¿Qué pregunta sobraba o faltaba?
4. ¿Pagarías por ayuda para implementar esa primera automatización?
5. ¿Preferirías hacerlo en cohort, acompañado o que alguien lo implemente?

## Criterios para decidir si está listo

Pasa beta si:

- 70% completa el diagnóstico.
- 60% genera informe.
- 40% deja feedback.
- Media de utilidad >= 4/5.
- Menos de 20% dice que el informe fue genérico.
- Al menos 3 leads piden cohort, acompañamiento o implementación.

No pasa beta si:

- La mayoría no sabe qué responder en la primera pregunta.
- El agente repite preguntas o alarga demasiado.
- El informe recomienda automatizaciones peligrosas sin revisión humana.
- La gente no entiende el siguiente paso.
- El CRM no permite operar los leads con claridad.

## Experimentos rápidos

Prueba tres entradas distintas:

- YouTube WhatsApp: “Descubre si tu primer empleado IA debería atender WhatsApp, leads o reservas.”
- Newsletter: “Te regalo un diagnóstico para saber dónde se te escapa tiempo, dinero o clientes.”
- LinkedIn/manual: “Estoy probando un consultor IA que detecta procesos automatizables en pymes.”

Mide por fuente:

- Visita -> inicio.
- Inicio -> email.
- Email -> informe.
- Informe -> feedback.
- Informe -> respuesta/comentario solicitando ayuda.

## Decisión tras 10 pruebas

- Si el problema más repetido es email/leads/WhatsApp, crea una landing específica por caso de uso.
- Si los informes son buenos pero la gente no deja email, mejora el cierre antes del gate.
- Si dejan email pero no piden ayuda, cambia CTA a recurso/cohort.
- Si piden implementación, prepara oferta “Primer empleado IA en 14 días”.
