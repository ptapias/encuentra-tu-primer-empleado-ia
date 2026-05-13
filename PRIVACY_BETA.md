# Privacidad beta - Encuentra Tu Primer Empleado IA

Documento operativo para la beta. Debe revisarse antes de publicación definitiva y adaptarse con los datos reales del responsable.

## Información básica

| Punto | Información |
|---|---|
| Responsable | Pablo Tapias / Tu Primer Empleado IA. Completar razón social o datos fiscales antes de publicar. |
| Finalidad | Generar un diagnóstico personalizado de procesos automatizables, mostrar y guardar el informe, crear un enlace privado de acceso al diagnóstico, mejorar el producto con feedback y cualificar el siguiente paso comercial cuando proceda. |
| Datos tratados | Email, respuestas de la conversación, información de negocio aportada por la persona, informe generado, métricas de uso y feedback. |
| Base | Consentimiento de la persona al completar el diagnóstico y solicitar el informe. Revisar encaje legal antes de escalar la beta. |
| Destinatarios | No vender datos. Puede haber proveedores técnicos de hosting, email, CRM/webhook, IA o transcripción necesarios para prestar el servicio y operar la beta. |
| Conservación | Durante la beta, conservar solo el tiempo necesario para generar el informe, revisar calidad, dar seguimiento y aprender del producto. Definir plazo concreto antes de lanzamiento público amplio. |
| Derechos | La persona puede pedir acceso, rectificación, supresión, oposición, limitación o portabilidad escribiendo al email de contacto que se defina. |
| Contacto | Completar email de privacidad/contacto antes de publicar. |

## Texto corto para el punto de recogida

Usaremos tu email y la conversación para generar, mostrar y guardar el diagnóstico, crear un enlace privado de acceso al informe, mejorar esta beta y, si encaja, proponerte el siguiente paso. No vendemos tus datos. Puedes pedir que eliminemos tu información escribiéndonos.

## Capa adicional recomendada

Antes de abrir tráfico público, completar:

- Identidad legal completa del responsable.
- Email de contacto para derechos de privacidad.
- Proveedores reales usados: hosting, email, CRM, IA/transcripción.
- Si se configura `CRM_WEBHOOK_URL`, identificar el destino concreto del webhook y qué datos recibirá.
- Plazo de conservación concreto.
- Si se usarán datos para newsletter aparte del diagnóstico, separarlo claramente del envío del informe.
- Si habrá decisiones comerciales automatizadas, explicarlo; la recomendación actual es mantener revisión humana.

## Operación de solicitudes de eliminación

Durante la beta, si una persona pide borrar sus datos:

1. Abrir `CRM_Dashboard.html`.
2. Localizar el lead por email o conversación.
3. Usar `Borrar lead` y confirmar escribiendo `DELETE`.
4. Ejecutar un backup después si el borrado forma parte de una limpieza operativa.

El borrado elimina el lead y sus eventos asociados de SQLite. Los backups históricos deben gestionarse según el plazo de conservación que se defina antes del lanzamiento público amplio.

## Referencias usadas

- AEPD: deber de información e información por capas.
- AEPD: guía/modelo de cláusula informativa.
