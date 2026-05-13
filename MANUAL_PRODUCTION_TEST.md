# Prueba manual de producción

Usa este documento después de desplegar en VPS y antes de pasar el enlace a testers externos.

## Datos de la prueba

| Campo | Valor |
|---|---|
| Fecha |  |
| Dominio probado |  |
| Commit `/healthz.version` |  |
| Tester |  |
| Dispositivo | Escritorio / móvil |
| Navegador |  |
| Origen/UTM usado |  |

## Prechecks

| Check | Esperado | Resultado | Evidencia |
|---|---|---|---|
| `DOMAIN=... ./deploy/verify_vps.sh` | Pasa sin errores |  |  |
| `/healthz` | `ok=true`, `provider=codex/openai`, `version` correcto |  |  |
| CRM sin login | Devuelve `401` o pide credenciales |  |  |
| CRM con login | Carga dashboard y métricas |  |  |
| Página pública | No pide email al inicio |  |  |
| Privacidad | No contiene placeholders ni notas de beta interna |  |  |

## Flujo de diagnóstico

| Paso | Esperado | Resultado | Evidencia |
|---|---|---|---|
| Abrir landing | Hero “¿Dónde se te escapa tiempo, dinero o clientes?” visible |  |  |
| Posicionamiento consultivo | Se ve “Discovery gratuito · 7-10 min”, “mini sesión consultiva” y “Empieza con una escena real” |  |  |
| Discovery en vivo | Se ve bloque “Discovery en vivo” y queda claro que no es un formulario |  |  |
| Empezar diagnóstico | Se oculta starter, aparece chat y composer |  |  |
| Primer mensaje | Pide contexto de negocio de forma conversacional |  |  |
| Responder por texto | El agente responde adaptándose al caso |  |  |
| Espera larga | Se muestra contador/mensaje de espera, no parece congelado |  |  |
| Progreso lateral | Foco, claridad, señales y gaps se actualizan |  |  |
| Micrófono HTTPS | Pide permiso, graba, transcribe y añade texto |  |  |
| Discovery adaptativa | Repregunta según la respuesta real y no sigue un guion fijo |  |  |
| Cierre discovery | Cierra cuando tiene suficiente, sin repetir preguntas |  |  |
| Email-gate | Pide email solo al final y exige consentimiento |  |  |
| Informe | Genera diagnóstico con oportunidades y recomendación principal |  |  |
| Matriz | Se ve impacto frente a factibilidad |  |  |
| Evidencia | Se ven señales detectadas y “por qué esta va primero” |  |  |
| Plan | Aparece plan de 7/30 días |  |  |
| PDF | “Guardar PDF” abre/imprime una versión limpia |  |  |
| Enlace privado | “Copiar enlace privado” abre `/r/...`, muestra informe y no expone email/conversación |  |  |
| CTA | “Me interesa este siguiente paso” guarda intención |  |  |
| Feedback | Rating y texto se guardan sin error |  |  |

## Revisión CRM

| Campo | Esperado | Resultado | Evidencia |
|---|---|---|---|
| Lead nuevo | Aparece en la lista con origen/campaña |  |  |
| Conversación | Transcript completo visible |  |  |
| Consentimiento | `accepted=true` y versión de privacidad |  |  |
| Outcome | Resumen, empleado IA recomendado y top oportunidades |  |  |
| Señales | Evidence summary visible |  |  |
| CTA interest | Segmento guardado |  |  |
| Feedback | Rating, utilidad, claridad y faltantes guardados |  |  |
| Latencia IA | Métrica de chat/informe aparece en dashboard |  |  |
| CSV | Export incluye email, consentimiento, CTA, feedback y evidencia |  |  |
| Borrado | Si se prueba, elimina lead y eventos asociados |  |  |

## Pruebas mínimas antes de abrir

Completar al menos:

- 1 diagnóstico en escritorio.
- 1 diagnóstico en móvil.
- 1 prueba real de micrófono en HTTPS.
- 1 export CSV revisado.
- 1 acceso CRM sin credenciales rechazado.
- 1 lead revisado en CRM de punta a punta.

## Go / no-go

Abrir beta controlada solo si:

- El verificador VPS pasa.
- El CRM está protegido.
- La privacidad final está generada con datos reales.
- El micrófono funciona en HTTPS o el copy no lo presenta como vía principal.
- Los dos diagnósticos manuales generan informes útiles.
- No hay datos internos expuestos públicamente.

No abrir si:

- Codex falla como usuario de servicio.
- El informe queda vacío, genérico o tarda de forma inaceptable.
- El email/consentimiento no quedan guardados.
- El CRM o CSV exponen datos sin autenticación.
- El dominio no usa HTTPS.

## Notas y decisión

Resultado final: Abrir / No abrir

Notas:

-
