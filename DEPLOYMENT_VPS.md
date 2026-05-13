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
ADMIN_USER=admin
ADMIN_PASSWORD=una-password-larga
```

## 3. Servicio

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
```

## 4. HTTPS con Caddy

Edita `deploy/Caddyfile.example` con el dominio real y cópialo:

```bash
sudo cp deploy/Caddyfile.example /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

## 5. URLs

- Público: `https://diagnostico.tu-dominio.com/Agente_Real_CRM.html`
- CRM: `https://diagnostico.tu-dominio.com/CRM_Dashboard.html`

Smoke test público tras activar el dominio:

```bash
python3 test_beta_smoke.py --base https://diagnostico.tu-dominio.com --admin-user admin --admin-password una-password-larga
```

## 6. Operación de beta

- Revisa el CRM una vez al día.
- Mira las métricas superiores del CRM: inicio de conversación, captura de email, informes generados, feedback y media de turnos.
- Exporta manualmente `crm.sqlite3` como backup.
- Mira logs con `journalctl -u primer-empleado-ia -f`.
- Si Codex CLI falla o tarda demasiado, cambia a `AI_PROVIDER=openai` temporalmente.

## 7. Riesgos conocidos

- Codex CLI no está pensado como backend público de alto tráfico.
- Cada turno puede tardar 9-15 segundos y cada informe 30-60 segundos.
- Para tráfico abierto conviene cola asíncrona, límites más estrictos o API dedicada.
