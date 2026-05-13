# Despliegue en VPS

Esta guía deja la beta privada funcionando con Codex CLI como proveedor de IA.

## 1. Preparar servidor

```bash
sudo adduser --system --group --home /opt/primer-empleado-ia primeria
sudo mkdir -p /opt/primer-empleado-ia
sudo chown -R primeria:primeria /opt/primer-empleado-ia
```

Instala Python 3.10+ y Caddy. Instala Codex CLI y ejecuta login en el servidor con la cuenta que quieras usar para la beta interna:

```bash
codex login
codex exec --skip-git-repo-check --ephemeral 'Responde solo: ok'
```

## 2. Subir aplicación

```bash
git clone https://github.com/ptapias/encuentra-tu-primer-empleado-ia.git /opt/primer-empleado-ia
sudo chown -R primeria:primeria /opt/primer-empleado-ia
cd /opt/primer-empleado-ia
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
MAX_AI_CONCURRENCY=1
AI_QUEUE_WAIT_SECONDS=8
BETA_NOINDEX=true
WHISPER_BIN=/usr/local/bin/whisper
FFMPEG_BIN=/usr/bin/ffmpeg
```

Si no vas a usar micrófono en la primera beta, la app seguirá funcionando por texto. El endpoint `/api/capabilities` indicará si la transcripción está disponible y la UI desactivará el botón de micro si faltan binarios.

Antes de arrancar el servicio, ejecuta el preflight:

```bash
python3 preflight_vps.py --env .env
```

Si quieres comprobar también que Codex CLI está logueado y responde:

```bash
python3 preflight_vps.py --env .env --check-codex-live
```

También puedes ejecutar el chequeo de release. Este comando agrupa sintaxis, copy público, privacidad beta, preflight y, si la app ya está arrancada, smoke test:

```bash
python3 release_check.py --env .env --check-codex-live
```

## 3. Servicio

El servicio queda limitado a `/opt/primer-empleado-ia` con hardening básico de systemd. La app debe escuchar en `127.0.0.1` y exponerse solo a través de Caddy/HTTPS.

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

Edita `deploy/Caddyfile.example` con el dominio real y cópialo. El ejemplo incluye proxy local, límite de cuerpo de 2 MB y headers básicos de seguridad:

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

Para una apertura pública más allá de beta controlada, completa antes `PRIVACY_BETA.md` y usa:

```bash
python3 release_check.py --env .env --base https://diagnostico.tu-dominio.com --admin-user admin --admin-password una-password-larga --require-privacy-final
```

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

## 7. Riesgos conocidos

- Codex CLI no está pensado como backend público de alto tráfico.
- Cada turno puede tardar 9-15 segundos y cada informe 30-60 segundos.
- Para tráfico abierto conviene cola asíncrona, límites más estrictos o API dedicada.
