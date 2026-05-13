# Validación local antes de VPS

## 1. Arrancar en modo rápido

Usa este modo para comprobar interfaz, email-gate, CRM e informe sin esperar a Codex:

```bash
AI_PROVIDER=fallback HOST=localhost PORT=8787 python3 app_server.py
```

Abre:

```text
http://localhost:8787/Agente_Real_CRM.html?v=discovery
```

Comprueba:

- La página empieza sin pedir email.
- El botón visible es `Analizar mi negocio`.
- No aparecen textos como `JSON`, `CRM`, `fallback` o `informe potente`.
- Al empezar aparece `Lo que estoy entendiendo`.
- El botón `Ver mi diagnóstico` no aparece hasta que el agente decide que tiene suficiente.
- El email se pide solo antes de generar el diagnóstico.

## 2. Arrancar con Codex real

Usa este modo para probar calidad de conversación:

```bash
AI_PROVIDER=codex HOST=localhost PORT=8787 python3 app_server.py
```

Cada turno puede tardar 9-20 segundos. El diagnóstico puede tardar 30-90 segundos.

## 3. Ejecutar pruebas de producto

Con el servidor arrancado:

```bash
python3 test_discovery_flow.py
```

El script simula:

- clínica dental,
- inmobiliaria,
- consultor B2B.

La prueba falla si el agente no devuelve:

- respuesta natural,
- foco actual,
- gaps abiertos,
- insights vivos,
- procesos candidatos,
- diagnóstico con empleado recomendado,
- oportunidades,
- plan de 7 días.

## 4. Criterio mínimo para pasar a VPS

Antes de subirlo:

- 3 casos del script pasan.
- 2 pruebas manuales con voz pasan.
- El CRM interno muestra conversación, diagnóstico y feedback.
- No hay textos internos en la página pública.
- Codex CLI funciona en la máquina destino o se decide usar API.
