# Inputs para desplegar en VPS

Rellena esta ficha antes de ejecutar `DEPLOYMENT_VPS.md`. La idea es evitar decisiones improvisadas mientras estamos conectados al servidor.

No escribas contraseñas ni datos legales reales en este archivo versionado. Crea una copia local ignorada por Git:

```bash
cp VPS_INPUTS.md VPS_INPUTS.local.md
python3 validate_vps_inputs.py --path VPS_INPUTS.local.md
```

## Acceso y dominio

- Dominio/subdominio público:
- IP del VPS:
- Usuario SSH:
- Puerto SSH:
- Sistema operativo:
- ¿El dominio ya apunta al VPS?:
- Ruta de instalación:
  - Valor por defecto: `/opt/primer-empleado-ia`

## IA y transcripción

- Proveedor IA inicial:
  - Recomendado para beta controlada: `codex`
  - Alternativa estable para tráfico: `openai`
- Ruta de Codex CLI en VPS:
  - Posible valor: `/usr/local/bin/codex`
- Usuario systemd que tendrá sesión Codex:
  - Valor por defecto: `primeria`
- ¿Codex CLI ya está logueado con ese usuario?:
- ¿El micro entra en la primera beta?:
  - `sí`: instalar y validar `ffmpeg` + `whisper`, probar HTTPS.
  - `no`: usar `--mic-optional` y no presentar el micro como vía principal.

## CRM y seguridad

- Usuario admin CRM:
  - Valor por defecto: `admin`
- Contraseña real CRM:
- ¿Webhook externo desde el día 1?:
- Destino webhook:
  - Make / n8n / Zapier / Airtable / HubSpot / otro:
- URL webhook:
- Secreto webhook:
- ¿Enviar conversación completa al webhook?:

## Privacidad

- Responsable legal:
- NIF/CIF o razón social:
- Email de contacto privacidad:
- Proveedor VPS/hosting:
- Proveedor IA:
- Proveedor transcripción:
- Proveedor email:
- Destino CRM/webhook:
- Plazo de conservación:
  - Recomendación beta: `6 meses desde la última interacción, salvo solicitud de supresión previa`.
- ¿El diagnóstico suscribe automáticamente a newsletter?:
  - Recomendación: `No; solo con consentimiento separado`.

## Variables `.env` objetivo

```bash
HOST=127.0.0.1
PORT=8787
AI_PROVIDER=codex
CODEX_BIN=/usr/local/bin/codex
ALLOW_AI_FALLBACK=false
APP_VERSION=
WHISPER_BIN=/usr/local/bin/whisper
FFMPEG_BIN=/usr/bin/ffmpeg
ADMIN_USER=admin
ADMIN_PASSWORD=
CRM_WEBHOOK_URL=
CRM_WEBHOOK_SECRET=
CRM_WEBHOOK_TIMEOUT=5
MAX_PUBLIC_EVENTS_PER_HOUR=80
MAX_MESSAGE_CHARS=3500
MAX_USER_TURNS=14
MAX_BODY_BYTES=1200000
MAX_AI_CONCURRENCY=1
AI_QUEUE_WAIT_SECONDS=8
BETA_NOINDEX=true
OPENAI_MODEL=gpt-4.1-mini
OPENAI_API_KEY=
```

## Decisión de apertura

No abrir a testers externos hasta que todo esto sea cierto:

- Dominio HTTPS carga el diagnóstico.
- CRM pide contraseña.
- `release_check.py --public-beta` pasa.
- `launch_go_no_go.py --public-beta` pasa.
- Se hicieron 2 pruebas manuales reales, una en escritorio y otra en móvil.
- El CRM muestra conversación, consentimiento, outcome, CTA y feedback.
- El CSV incluye email, consentimiento, CTA, feedback, evidencia y discovery viva.
- Si el micro se anuncia, funciona en HTTPS.
