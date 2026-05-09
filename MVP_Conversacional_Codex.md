# MVP conversacional: versión correcta

## Cambio de criterio

El MVP anterior era demasiado formulario. No representa bien la promesa de "Encuentra Tu Primer Empleado IA".

La experiencia correcta debe sentirse como una entrevista de diagnóstico:

- El usuario escribe en lenguaje natural.
- El agente escucha y resume lo que entiende.
- El agente repregunta cuando algo está vago.
- El agente tira del hilo hacia procesos, herramientas, datos, volumen, riesgo e impacto.
- El agente no salta a recomendar herramientas.
- El agente termina con un informe personalizado y pide feedback.

## Promesa actualizada

"Habla con un agente que analiza tu negocio como lo haría un consultor: entiende tus procesos, detecta dónde pierdes tiempo o ventas, y te recomienda cuál debería ser tu primer empleado IA."

## Qué debe sentir el usuario

No debe sentir que rellena un cuestionario.

Debe sentir:

- "Me está entendiendo".
- "Me está haciendo preguntas que no me había hecho".
- "Está bajando mi caos a procesos concretos".
- "No intenta venderme IA para todo".
- "Me dice qué automatizar y qué no".

## Arquitectura realista con Codex

### Lo que no se puede hacer

Una web pública no puede usar directamente tu suscripción personal de Codex como si fuera una API para atender usuarios finales en tiempo real.

Motivos:

- Codex está pensado para sesiones de trabajo, no para servir tráfico público.
- Exponer tu sesión o credenciales en una web sería inseguro.
- No hay un endpoint público estable para que visitantes anónimos conversen contra tu suscripción.
- Cada conversación pública necesitaría aislamiento, límites, logging, privacidad y control de abuso.

### Lo que sí se puede hacer sin API al inicio

**Opción A: Codex-operated, asíncrono**

1. La web tiene un chat conversacional propio.
2. El chat recoge una transcripción rica.
3. El usuario recibe un resultado preliminar.
4. Las conversaciones se guardan en Airtable/Sheets/Supabase.
5. Tú usas Codex para procesar lotes, revisar casos interesantes y generar informes mejores.
6. Envías informes ampliados manualmente o semi-manualmente.

Ventaja: no pagas API y aprendes rápido.  
Desventaja: no es IA real en tiempo real para el usuario.

**Opción B: Codex local para pruebas privadas**

1. Ejecutas una app local en tu Mac.
2. La app invoca `codex exec` con el prompt y la transcripción.
3. Tú pruebas la experiencia con casos propios o usuarios cercanos.

Ventaja: usa tu entorno local.  
Desventaja: no sirve para web pública abierta.

**Opción C: Producción real con API**

1. Web pública con chat.
2. Backend propio.
3. LLM por API con límites de coste.
4. Guardado de conversación, scoring e informe.
5. Feedback final.

Ventaja: experiencia real.  
Desventaja: hay coste API, aunque controlable.

## Recomendación

Para validar sin API:

1. Publicar una versión conversacional con lógica propia y resultado preliminar.
2. Guardar transcripción y feedback.
3. Procesar manualmente con Codex los primeros 30-50 casos.
4. Identificar qué preguntas generan mejores diagnósticos.
5. Solo entonces automatizar con API.

Si quieres una experiencia "wow" desde el día 1, hay que asumir API. No hace falta que sea caro si se diseña bien:

- Modelo barato para entrevista.
- Plantillas de scoring.
- Informe estructurado.
- Límite de turnos.
- Máximo de tokens por conversación.
- Solo generar informe largo si el usuario deja email y completa feedback.

## Diseño de conversación

### Fase 1: contexto

Objetivo: entender negocio y cliente.

Preguntas:

- ¿A qué se dedica tu negocio y quién es tu cliente principal?
- ¿Cómo llega hoy un cliente hasta ti?
- ¿Trabajas solo o hay equipo?

### Fase 2: mapa de procesos

Objetivo: encontrar repetición.

Preguntas:

- Cuéntame una tarea que repitas todas las semanas y te quite energía.
- ¿Qué pasa antes, durante y después de esa tarea?
- ¿Qué parte depende demasiado de ti?

### Fase 3: ejemplo concreto

Objetivo: evitar abstracción.

Preguntas:

- Dame un ejemplo real de la última vez que ocurrió.
- ¿Qué información entró?
- ¿Qué tuviste que decidir?
- ¿Qué salida esperabas?

### Fase 4: datos y herramientas

Objetivo: saber si se puede construir.

Preguntas:

- ¿Dónde vive hoy la información?
- ¿Qué herramientas usas?
- ¿Tienes ejemplos reales de emails, WhatsApps, propuestas, tickets o documentos?

### Fase 5: riesgo

Objetivo: no recomendar barbaridades.

Preguntas:

- Si una IA se equivoca aquí, ¿qué sería lo peor razonable?
- ¿Qué cosas debería revisar siempre una persona?
- ¿Cuándo habría que escalar a humano?

### Fase 6: priorización

Objetivo: conectar con negocio.

Preguntas:

- ¿Qué pasa si esto sigue igual 3 meses?
- ¿Esto te cuesta tiempo, ventas, calidad o foco?
- ¿Quieres aprender a montarlo, hacerlo acompañado o que alguien lo implemente?

### Fase 7: informe y feedback

Output:

- Lo que he entendido de tu negocio.
- Dónde veo la oportunidad.
- Qué empleado IA construiría primero.
- Qué haría y qué no haría.
- Qué datos necesita.
- Qué riesgos hay.
- Primer paso.
- Feedback: utilidad, claridad, faltantes y mejoras.

## Nuevo artefacto

El archivo `Prototipo_Conversacional.html` sustituye al prototipo tipo formulario como demostración de experiencia.

## Añadidos de la versión actual

- Dictado por micrófono mediante Web Speech API del navegador.
- Botón de micrófono como icono, sin texto visible.
- Indicador superior de fase: contexto, proceso, ejemplo real, herramientas/datos, riesgo, impacto y cierre.
- Diagnóstico adaptativo: no hay cinco preguntas fijas. El agente cubre huecos de diagnóstico y puede alargarse si el caso lo necesita.
- Prompt de fondo separado en `Prompt_Investigacion_Procesos.md`.
- Evaluación de iniciativas con el framework `AI Use Case Evaluation Framework v0.2`.
- Gráfico de barras por iniciativa: impacto, factibilidad, escalabilidad y sensibilidad de datos.
- Triage de iniciativas: PROCEED, REFINE o PARK.
- Feedback final obligatorio para aprender qué mejorar.

## Nota sobre dictado

El dictado depende del navegador. En Chrome/Edge suele funcionar mejor. En algunos navegadores el botón aparecerá como no disponible. En producción conviene ofrecer también transcripción de audio por backend si el dictado nativo no es suficiente.
