# Preparación para producción

Este documento recoge lo que falta antes de mandar el diagnóstico a gente externa.

## Datos que necesito antes del VPS

- Dominio o subdominio final, por ejemplo `diagnostico.tuprimerempleadoia.com`.
- IP o acceso SSH al VPS.
- Ruta donde instalar la app, por defecto `/opt/primer-empleado-ia`.
- Usuario de GitHub con acceso al repo.
- Contraseña real para el CRM interno.
- Confirmación de proveedor IA:
  - `AI_PROVIDER=codex` si el VPS tendrá Codex CLI logueado.
  - `AI_PROVIDER=openai` si decides usar API más adelante.

## Datos legales mínimos

Completar antes de usar `--public-beta`:

- Responsable legal o datos fiscales.
- Email de contacto para privacidad.
- Proveedores reales usados: VPS/hosting, correo si aplica, IA/transcripción.
- Si se configura `CRM_WEBHOOK_URL`, proveedor/destino concreto del webhook y datos enviados.
- Plazo de conservación.
- Si los leads entran también a newsletter o solo al diagnóstico.
- Actualizar también `PRIVACY_BETA.html`; el gate falla si la página pública conserva notas de beta como “antes de abrir tráfico público amplio”.

Para evitar editar dos archivos a mano:

```bash
cp privacy_config.example.json privacy_config.json
nano privacy_config.json
python3 render_privacy.py --config privacy_config.json
```

Mientras esto no esté completo, `release_check.py --public-beta` debe fallar.

## Variables esperadas en `.env`

```bash
HOST=127.0.0.1
PORT=8787
AI_PROVIDER=codex
CODEX_BIN=/usr/local/bin/codex
ALLOW_AI_FALLBACK=false
ADMIN_USER=admin
ADMIN_PASSWORD=una-password-larga
CRM_WEBHOOK_URL=
CRM_WEBHOOK_SECRET=
CRM_WEBHOOK_TIMEOUT=5
MAX_AI_CONCURRENCY=1
AI_QUEUE_WAIT_SECONDS=8
BETA_NOINDEX=true
WHISPER_BIN=/usr/local/bin/whisper
FFMPEG_BIN=/usr/bin/ffmpeg
```

## Comando de apertura pública

Este es el gate final. Si falla, no se abre la beta:

```bash
python3 release_check.py \
  --env .env \
  --base https://diagnostico.tu-dominio.com \
  --admin-user admin \
  --admin-password una-password-larga \
  --public-beta
```

Para obtener un veredicto operativo en una sola salida:

```bash
python3 launch_go_no_go.py \
  --env .env \
  --base https://diagnostico.tu-dominio.com \
  --admin-user admin \
  --admin-password una-password-larga \
  --public-beta \
  --check-codex-live \
  --service-user primeria \
  --with-browser \
  --with-transcription \
  --manual-production-tested \
  --crm-reviewed \
  --mic-tested
```

Si decides lanzar una beta por texto aunque el micro no esté validado en HTTPS, sustituye `--mic-tested` por `--mic-optional` y asegúrate de que el copy no presente el dictado como vía principal.

Debe validar:

- App viva en HTTPS.
- CRM protegido.
- Privacidad final sin placeholders.
- Codex CLI respondiendo en vivo como el usuario systemd (`primeria` por defecto), si se usa `AI_PROVIDER=codex`.
- Página pública sin textos internos.
- Email y consentimiento obligatorios antes del informe.
- Informe bloqueado si se llama a la API sin consentimiento.
- CTA de interés guardado en CRM/CSV.
- Archivos sensibles no expuestos.

## Prueba manual obligatoria

Después del despliegue:

- Abrir la web en móvil y escritorio.
- Hacer una conversación real de 7-10 minutos.
- Probar micrófono en HTTPS.
- Generar informe.
- Aceptar consentimiento.
- Marcar interés en el CTA.
- Dejar feedback.
- Revisar que todo aparece en CRM.
- Exportar CSV y comprobar email, consentimiento, CTA, feedback y origen.

Usa `MANUAL_PRODUCTION_TEST.md` para registrar resultado, evidencia y decisión de apertura.

No rellenes la plantilla versionada con evidencias reales. Crea una copia local ignorada por Git y valídala:

```bash
cp MANUAL_PRODUCTION_TEST.md MANUAL_PRODUCTION_TEST.local.md
nano MANUAL_PRODUCTION_TEST.local.md
python3 validate_manual_production_test.py --path MANUAL_PRODUCTION_TEST.local.md
```

## Decisión de salida

Abrir beta controlada si:

- El gate público pasa.
- El micrófono funciona en HTTPS.
- El CRM está protegido con contraseña real.
- La privacidad está finalizada.
- Se han hecho al menos 2 pruebas manuales reales en producción.

No abrir si:

- Codex CLI falla en el VPS.
- El informe tarda demasiado o queda atascado.
- El CRM es accesible sin auth.
- El dominio no tiene HTTPS.
- El email/consentimiento no quedan registrados.
