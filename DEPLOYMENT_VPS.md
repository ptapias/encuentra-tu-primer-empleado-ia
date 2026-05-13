# Despliegue en VPS

Esta guía deja la beta privada funcionando con Codex CLI como proveedor de IA.

## 1. Preparar servidor

```bash
sudo adduser --system --group --home /opt/primer-empleado-ia primeria
sudo mkdir -p /opt/primer-empleado-ia
sudo chown -R primeria:primeria /opt/primer-empleado-ia
```

Instala Python 3.10+ y Caddy. Instala Codex CLI y ejecuta login con el usuario que ejecutará el servicio (`primeria` por defecto). Esto es importante: si haces login como `root` pero systemd corre como `primeria`, el agente puede fallar aunque el preflight básico pase.

```bash
sudo -H -u primeria codex login
sudo -H -u primeria codex exec --skip-git-repo-check --ephemeral 'Responde solo: ok'
```

El validador de lanzamiento bloqueará la instalación guiada si eliges `AI_PROVIDER=codex` y marcas que Codex todavía no está logueado con ese usuario.

## 2. Subir aplicación

```bash
git clone https://github.com/ptapias/encuentra-tu-primer-empleado-ia.git /opt/primer-empleado-ia
sudo chown -R primeria:primeria /opt/primer-empleado-ia
cd /opt/primer-empleado-ia
```

Ruta recomendada: genera primero la ficha local guiada. El archivo queda ignorado por Git:

```bash
python3 generate_vps_inputs.py
python3 validate_vps_inputs.py --path VPS_INPUTS.local.md
python3 prepare_vps_launch_files.py --inputs VPS_INPUTS.local.md
```

El validador también bloquea el lanzamiento HTTPS si el dominio todavía no apunta al VPS. Cambia DNS antes de ejecutar el lanzador con `DOMAIN=...`.

La contraseña del CRM y los secretos que acaban en `.env` deben ser largos pero compatibles con systemd: sin espacios, comillas, `#` ni barras invertidas.

Después usa el lanzador desde la raíz del repo. Si existe `.env.generated`, lo usa para crear `.env`, renderiza privacidad, instala servicios, activa backup y valida Caddy:

```bash
sudo env DOMAIN=diagnostico.tu-dominio.com ./deploy/launch_from_inputs.sh
```

No crees `.env` antes de usar el lanzador guiado: si `.env` ya existe, el instalador la conserva y no copiará `.env.generated`.

Si decides saltarte el flujo guiado, entonces crea `.env` manualmente:

```bash
cp .env.example .env
```

Edita `.env`:

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

Cuando `.env` ya esté completo, instala servicios con dominio:

```bash
sudo env DOMAIN=diagnostico.tu-dominio.com ./deploy/install_vps.sh
```

`CRM_WEBHOOK_URL` es opcional. Úsalo si quieres enviar automáticamente email capturado, informe, interés CTA y feedback a Make, n8n, Zapier, Airtable, HubSpot u otro CRM.

Si configuras el CRM externo después de lanzar la beta o quieres reintentar envíos, puedes reenviar los leads existentes desde el VPS:

```bash
cd /opt/primer-empleado-ia
sudo -u primeria CRM_WEBHOOK_URL="https://tu-webhook" CRM_WEBHOOK_SECRET="tu-secreto" python3 sync_crm_webhook.py --limit 100
```

Para no enviar la conversación completa al CRM externo:

```bash
sudo -u primeria CRM_WEBHOOK_URL="https://tu-webhook" python3 sync_crm_webhook.py --no-transcript --limit 100
```

Si no vas a usar micrófono en la primera beta, la app seguirá funcionando por texto. El endpoint `/api/capabilities` indicará si la transcripción está disponible y la UI desactivará el botón de micro si faltan binarios.

Antes de abrir tráfico externo, genera la privacidad pública con datos reales:

```bash
cp privacy_config.example.json privacy_config.json
nano privacy_config.json
python3 render_privacy.py --config privacy_config.json
```

No uses el ejemplo tal cual: si conserva `Completar`, el generador falla.

Antes de arrancar el servicio, ejecuta el preflight:

```bash
python3 preflight_vps.py --env .env
```

Si quieres comprobar también que Codex CLI está logueado y responde:

```bash
sudo python3 preflight_vps.py --env .env --service-user primeria --check-codex-live
```

También puedes ejecutar el chequeo de release. Este comando agrupa sintaxis, copy público, privacidad beta, preflight y, si la app ya está arrancada, smoke test:

```bash
python3 release_check.py --env .env --check-codex-live
```

## 3. Servicio

El servicio queda limitado a `/opt/primer-empleado-ia` con hardening básico de systemd. La app debe escuchar en `127.0.0.1` y exponerse solo a través de Caddy/HTTPS. Si usas otra carpeta o usuario, usa el instalador automático; renderiza las unidades con `APP_DIR`, `APP_USER` y `APP_GROUP`.

```bash
sudo cp deploy/primer-empleado-ia.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable primer-empleado-ia
sudo systemctl start primer-empleado-ia
sudo systemctl status primer-empleado-ia
```

Comprueba:

```bash
curl http://127.0.0.1:8787/healthz
python3 test_beta_smoke.py --base http://127.0.0.1:8787 --admin-user admin --admin-password una-password-larga
python3 release_check.py --env .env --base http://127.0.0.1:8787 --admin-user admin --admin-password una-password-larga
```

La respuesta de `/healthz` incluye `version`. Déjalo como `APP_VERSION=` en `.env` para que use el commit corto de Git capturado al arrancar el servidor, o rellénalo con una etiqueta tipo `beta-2026-05-13` si quieres identificar despliegues manuales. Reinicia siempre el servicio después de actualizar código; el preflight avisa si `APP_VERSION` parece un commit antiguo y no coincide con el HEAD desplegado.

Activa también el backup diario del CRM:

```bash
sudo cp deploy/primer-empleado-ia-backup.service /etc/systemd/system/
sudo cp deploy/primer-empleado-ia-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now primer-empleado-ia-backup.timer
sudo systemctl list-timers primer-empleado-ia-backup.timer
sudo systemctl start primer-empleado-ia-backup.service
ls -lah backups/
```

## 4. HTTPS con Caddy

Edita `deploy/Caddyfile.example` con el dominio real y cópialo. El ejemplo incluye proxy local, límite de cuerpo de 2 MB, permiso explícito de micrófono para el propio dominio y headers básicos de seguridad:

```bash
sudo cp deploy/Caddyfile.example /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

## 5. URLs

- Público: `https://diagnostico.tu-dominio.com/Agente_Real_CRM.html`
- CRM: `https://diagnostico.tu-dominio.com/CRM_Dashboard.html`

Smoke test público tras activar el dominio:

```bash
python3 test_beta_smoke.py --base https://diagnostico.tu-dominio.com --admin-user admin --admin-password una-password-larga
python3 release_check.py --env .env --base https://diagnostico.tu-dominio.com --admin-user admin --admin-password una-password-larga
```

También puedes ejecutar el verificador completo del VPS. Lee la contraseña desde `.env`, prueba preflight, smoke local, smoke HTTPS y release gate:

```bash
DOMAIN=diagnostico.tu-dominio.com ./deploy/verify_vps.sh
```

Si el VPS tiene Playwright/Chromium y transcripción disponibles, puedes sumar pruebas más cercanas a usuario real:

```bash
DOMAIN=diagnostico.tu-dominio.com BROWSER_CHECKS=true TRANSCRIPTION_CHECK=true ./deploy/verify_vps.sh
```

Para una apertura pública más allá de beta controlada, completa antes `PRIVACY_BETA.md` y `PRIVACY_BETA.html`, y usa:

```bash
python3 release_check.py --env .env --base https://diagnostico.tu-dominio.com --admin-user admin --admin-password una-password-larga --public-beta
```

O con el verificador:

```bash
DOMAIN=diagnostico.tu-dominio.com \
PUBLIC_BETA=true \
BROWSER_CHECKS=true \
TRANSCRIPTION_CHECK=true \
MANUAL_PRODUCTION_TESTED=true \
MANUAL_TEST_PATH=MANUAL_PRODUCTION_TEST.local.md \
CRM_REVIEWED=true \
MIC_TESTED=true \
./deploy/verify_vps.sh
```

Ese gate falla si el dominio no usa HTTPS, si estás probando contra localhost, si no pasas credenciales reales del CRM, si la contraseña no coincide con `.env`, si la privacidad final sigue con placeholders o notas públicas de beta, si Codex CLI no responde en vivo, si no hay evidencia manual validada o si falta confirmar revisión de CRM/micro. Si el micro queda fuera de la primera beta, usa `MIC_OPTIONAL=true` en lugar de `MIC_TESTED=true`.

## 6. Operación de beta

- Revisa el CRM una vez al día.
- Mira las métricas superiores del CRM: inicio de conversación, captura de email, informes generados, feedback y media de turnos.
- Mantén `MAX_AI_CONCURRENCY=1` en beta con Codex CLI para evitar que varios diagnósticos simultáneos saturen el VPS. Si el agente está ocupado, el usuario verá un mensaje para reintentar en unos segundos.
- Mantén `BETA_NOINDEX=true` mientras sea beta privada o semi-privada. Cuando quieras que Google indexe la herramienta, cámbialo a `false` y reinicia el servicio.
- Si alguien pide eliminar sus datos, abre el CRM, selecciona el lead y usa `Borrar lead`; esto elimina el lead y sus eventos asociados.
- Haz backup de CRM antes de cambios importantes. El timer diario debería cubrir el respaldo rutinario:

```bash
python3 backup_crm.py
journalctl -u primer-empleado-ia-backup.service -n 50 --no-pager
```

- Mira logs con `journalctl -u primer-empleado-ia -f`.
- Si Codex CLI falla o tarda demasiado, cambia a `AI_PROVIDER=openai` temporalmente.

## 7. Actualizar versión en VPS

Cuando haya cambios en `main`, actualiza sin tocar `.env`, CRM ni backups:

```bash
cd /opt/primer-empleado-ia
sudo ./deploy/update_vps.sh
```

Si ya generaste la privacidad final desde `privacy_config.json`, el script tolera que `PRIVACY_BETA.md` y `PRIVACY_BETA.html` estén modificados localmente: los restaura antes del `pull` y los vuelve a generar después desde `privacy_config.json`. Si hay cualquier otro cambio local, se detiene para no pisar trabajo manual del VPS.

Con verificación HTTPS después del reinicio:

```bash
cd /opt/primer-empleado-ia
sudo env DOMAIN=diagnostico.tu-dominio.com ./deploy/update_vps.sh
```

El script exige worktree limpio, hace backup antes de traer cambios, usa `git pull --ff-only`, ejecuta preflight, actualiza las unidades systemd según `APP_DIR`, `APP_USER` y `APP_GROUP`, reinicia systemd y corre smoke test local. Si el update falla después de moverse a un nuevo commit, intenta volver al commit anterior y reiniciar el servicio. Si pasas `DOMAIN`, llama también a `verify_vps.sh`.

## 8. Riesgos conocidos

- Codex CLI no está pensado como backend público de alto tráfico.
- Cada turno puede tardar 9-15 segundos y cada informe 30-60 segundos.
- Para tráfico abierto conviene cola asíncrona, límites más estrictos o API dedicada.
