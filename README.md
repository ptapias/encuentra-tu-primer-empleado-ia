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
- `Prototipo_Conversacional.html`: prototipo principal de chat conversacional con repreguntas, memoria, informe preliminar y feedback.
- `Prototipo_Diagnostico.html`: prototipo antiguo tipo formulario. Mantener solo como referencia secundaria.
- `Plan_Prueba_y_Hosting.md`: cómo probarlo, publicarlo gratis al inicio y qué hacer con la parte de Codex/API.

## Recomendación de lanzamiento

Lanzar primero la versión gratuita como experiencia conversacional adaptativa: el usuario habla en lenguaje natural, el agente decide la siguiente pregunta según lo que falta por entender, detecta procesos y entrega un informe preliminar con feedback al final. Objetivo normal: 7-10 minutos; puede alargarse a 12-15 preguntas si el caso lo necesita.

La versión actual incluye grabación por micrófono con transcripción local vía Whisper cuando se sirve con `app_server.py`, indicador de fase, matriz de evaluación basada en el framework `AI Use Case Evaluation Framework v0.2` e informe con iniciativas priorizadas.

Para probar el micrófono usa:

```bash
python3 app_server.py
```

Luego abre `http://localhost:8787/Prototipo_Conversacional.html`. Pulsa el icono de micrófono para grabar, vuelve a pulsarlo para transcribir y añadir el texto al campo.

Nota clave: una web pública no puede usar directamente tu suscripción personal de Codex como API. Sí puedes usar Codex para pruebas locales o para procesar manualmente conversaciones recogidas por la web durante la validación.
