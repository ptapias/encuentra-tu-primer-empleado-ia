# Plan de prueba y hosting

## Decisión actual

Lanzar gratuito al inicio. El objetivo principal no es monetizar el diagnóstico, sino:

- Validar si la promesa se entiende.
- Detectar sectores con más dolor.
- Recoger lenguaje literal de usuarios.
- Aprender qué echan en falta del informe.
- Cualificar leads para newsletter, cohort o implementación.

## Cómo probarlo ahora

1. Arranca el servidor local con `python3 app_server.py`.
2. Abre `http://localhost:8787/Prototipo_Conversacional.html` en el navegador.
3. Prueba primero escribiendo y luego grabando con el icono de micrófono.
4. Para el micrófono: pulsa una vez para grabar, habla, pulsa otra vez para transcribir.
5. Rellena el diagnóstico como si fueras 5 tipos de usuario:
   - Consultor saturado con seguimiento comercial.
   - Inmobiliaria con WhatsApp.
   - Ecommerce con soporte.
   - Agencia con reporting.
   - Profesional saturado de email.
6. Comprueba que el proceso se adapta: si hablas de ventas debe profundizar en ventas; si hablas de soporte debe profundizar en soporte.
7. Comprueba si el indicador superior avanza de forma razonable por las fases.
8. Genera el informe y revisa la matriz de iniciativas.
9. Completa el bloque de feedback final.
10. Ajusta preguntas o copy según lo que resulte confuso.

## Cómo publicarlo sin backend

Opción más rápida:

- Subir `Prototipo_Conversacional.html` a una página estática para enseñar la experiencia.
- Sustituir el guardado local por Supabase/Airtable/Sheets si quieres guardar conversaciones reales.
- Mantener el micrófono como mejora de experiencia. En local usa Whisper vía `/transcribe`; en producción habría que usar una API de transcripción o un backend propio.
- Guardar también el score del framework: impacto, factibilidad, escalabilidad, sensibilidad y triage.
- Enviar respuestas a Airtable/Google Sheets.
- Añadir una pantalla final con recomendación básica y feedback.

Esta opción no genera un informe largo con IA real en tiempo real, pero sirve para validar si la conversación, las repreguntas y el output inicial tienen tracción sin costes de API.

## Sobre usar tu suscripción de Codex

Una web pública no puede conectarse directamente a tu suscripción personal de Codex para atender usuarios finales. Codex funciona como entorno de trabajo y asistente dentro de tu sesión, no como un backend público que puedas llamar desde una landing.

Formas razonables de usar Codex sin pagar API al inicio:

1. Recoger respuestas con Tally/Typeform.
2. Guardarlas en Airtable/Sheets.
3. Exportar los leads más interesantes.
4. Usar Codex manualmente para generar o revisar informes de muestra.
5. Mejorar el prompt, scoring y copy con esos casos reales.

También puedes probar localmente un flujo más avanzado invocando `codex exec` con transcripciones descargadas, pero eso debe quedarse en uso privado. No lo expondría como backend público.

Cuando el diagnóstico demuestre tracción, pasar a API con límites:

- Generar solo el informe corto automáticamente.
- Limitar longitud de entrada y salida.
- Cachear resultados.
- Usar plantillas con variables y LLM solo para la síntesis.
- Poner presupuesto máximo diario.

## MVP recomendado sin coste de API

Fase 1:

- Landing gratuita.
- Chat conversacional.
- Repreguntas adaptativas basadas en señales.
- Recomendación preliminar basada en reglas.
- Feedback final.
- Base de datos en Airtable/Sheets.
- Emails manuales o beehiiv automation simple.

Fase 2:

- Revisar 50-100 respuestas.
- Identificar patrones por sector y caso de uso.
- Usar Codex para convertir respuestas reales en mejores informes.
- Crear 3 versiones verticales: WhatsApp, ventas/email y operaciones.

Fase 3:

- Automatizar informe corto con API.
- Mantener revisión humana solo para leads premium.

## Feedback final recomendado

Texto:

"Antes de irte: estoy mejorando este diagnóstico con casos reales. ¿Me ayudas con 30 segundos de feedback?"

Preguntas:

- Del 1 al 5, ¿te ha resultado útil?
- ¿Qué parte te ha dado más claridad?
- ¿Qué has echado en falta?
- ¿Qué pregunta te sobró o te resultó confusa?
- ¿Qué debería incluir una versión más completa?
- ¿Quieres que te avise cuando esté la versión mejorada?
