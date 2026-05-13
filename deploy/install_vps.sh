#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/primer-empleado-ia}"
APP_USER="${APP_USER:-primeria}"
APP_GROUP="${APP_GROUP:-${APP_USER}}"
DOMAIN="${DOMAIN:-}"
ADMIN_USER="${ADMIN_USER:-admin}"
CHECK_CODEX_LIVE="${CHECK_CODEX_LIVE:-true}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Ejecuta este script con sudo desde el VPS." >&2
  exit 1
fi

if [[ ! -f "app_server.py" || ! -d "deploy" ]]; then
  echo "Ejecuta desde la raíz del repo clonado: ${APP_DIR}" >&2
  exit 1
fi

if ! id "${APP_USER}" >/dev/null 2>&1; then
  adduser --system --group --home "${APP_DIR}" "${APP_USER}"
fi

mkdir -p "${APP_DIR}"

if [[ "$(pwd)" != "${APP_DIR}" ]]; then
  rsync -a --delete \
    --exclude ".env" \
    --exclude "crm.sqlite3" \
    --exclude "crm.sqlite3-*" \
    --exclude "crm_leads.jsonl" \
    --exclude "backups" \
    ./ "${APP_DIR}/"
fi

cd "${APP_DIR}"
mkdir -p backups

if [[ ! -f ".env" ]]; then
  if [[ -f ".env.generated" ]]; then
    cp .env.generated .env
    echo "He creado ${APP_DIR}/.env desde .env.generated." >&2
  else
    cp .env.example .env
    chown "${APP_USER}:${APP_GROUP}" .env
    chmod 600 .env
    echo "He creado ${APP_DIR}/.env desde .env.example. Edita ADMIN_PASSWORD, CODEX_BIN y dominio antes de arrancar." >&2
    exit 2
  fi
  chown "${APP_USER}:${APP_GROUP}" .env
  chmod 600 .env
fi

if grep -q '^ADMIN_PASSWORD=change-me$' .env || ! grep -q '^ADMIN_PASSWORD=.\+' .env; then
  echo "Configura una ADMIN_PASSWORD real en ${APP_DIR}/.env antes de publicar." >&2
  exit 3
fi

chown -R "${APP_USER}:${APP_GROUP}" "${APP_DIR}"
chmod 700 "${APP_DIR}"
chmod 600 "${APP_DIR}/.env"

PREFLIGHT=(python3 preflight_vps.py --env .env --service-user "${APP_USER}")
if [[ "${CHECK_CODEX_LIVE}" == "true" ]]; then
  PREFLIGHT+=(--check-codex-live)
fi
"${PREFLIGHT[@]}"
python3 release_check.py --env .env

APP_DIR="${APP_DIR}" APP_USER="${APP_USER}" APP_GROUP="${APP_GROUP}" ./deploy/render_systemd_units.sh
systemctl daemon-reload
systemctl enable primer-empleado-ia
systemctl restart primer-empleado-ia
systemctl enable --now primer-empleado-ia-backup.timer

if [[ -n "${DOMAIN}" ]]; then
  if ! command -v caddy >/dev/null 2>&1; then
    echo "Caddy no está instalado; omito configuración HTTPS." >&2
  else
    sed "s/diagnostico.tuprimerempleadoia.com/${DOMAIN}/g" deploy/Caddyfile.example > /etc/caddy/Caddyfile
    caddy validate --config /etc/caddy/Caddyfile
    systemctl reload caddy
  fi
fi

sleep 2
EXPECTED_VERSION="$(grep '^APP_VERSION=' .env | cut -d= -f2-)"
if [[ -z "${EXPECTED_VERSION}" ]] && command -v git >/dev/null 2>&1; then
  EXPECTED_VERSION="$(git rev-parse --short HEAD)"
fi
python3 test_beta_smoke.py --base http://127.0.0.1:8787 --admin-user "${ADMIN_USER}" --admin-password "$(grep '^ADMIN_PASSWORD=' .env | cut -d= -f2-)" --expected-version "${EXPECTED_VERSION}"

echo "Instalación local en VPS lista. Ejecuta el smoke test contra el dominio HTTPS cuando DNS/Caddy estén activos."
