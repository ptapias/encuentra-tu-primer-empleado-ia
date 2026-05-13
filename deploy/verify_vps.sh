#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/primer-empleado-ia}"
DOMAIN="${DOMAIN:-}"
ADMIN_USER="${ADMIN_USER:-admin}"
APP_USER="${APP_USER:-primeria}"
PUBLIC_BETA="${PUBLIC_BETA:-false}"
CHECK_CODEX_LIVE="${CHECK_CODEX_LIVE:-true}"

if [[ ! -d "${APP_DIR}" ]]; then
  echo "No existe APP_DIR=${APP_DIR}" >&2
  exit 1
fi

cd "${APP_DIR}"

if [[ ! -f ".env" ]]; then
  echo "Falta ${APP_DIR}/.env" >&2
  exit 1
fi

env_value() {
  local key="$1"
  awk -F= -v key="${key}" '$1 == key { sub(/^[^=]*=/, ""); gsub(/^'\''|'\''$/, ""); gsub(/^"|"$/, ""); print; exit }' .env
}

ADMIN_PASSWORD="${ADMIN_PASSWORD:-$(env_value ADMIN_PASSWORD)}"
HOST_VALUE="$(env_value HOST)"
PORT_VALUE="$(env_value PORT)"
PORT_VALUE="${PORT_VALUE:-8787}"
LOCAL_BASE="http://${HOST_VALUE:-127.0.0.1}:${PORT_VALUE}"

if [[ -z "${ADMIN_PASSWORD}" || "${ADMIN_PASSWORD}" == "change-me" ]]; then
  echo "ADMIN_PASSWORD no está configurada con un valor real." >&2
  exit 1
fi

PREFLIGHT=(python3 preflight_vps.py --env .env --service-user "${APP_USER}")
if [[ "${CHECK_CODEX_LIVE}" == "true" ]]; then
  PREFLIGHT+=(--check-codex-live)
fi

echo "1/4 Preflight VPS"
"${PREFLIGHT[@]}"

echo "2/4 Smoke local (${LOCAL_BASE})"
python3 test_beta_smoke.py \
  --base "${LOCAL_BASE}" \
  --admin-user "${ADMIN_USER}" \
  --admin-password "${ADMIN_PASSWORD}"

if [[ -z "${DOMAIN}" ]]; then
  echo "DOMAIN vacío: salto comprobaciones HTTPS públicas."
  echo "Verificación local completada. Para dominio público: DOMAIN=diagnostico.tu-dominio.com ./deploy/verify_vps.sh"
  exit 0
fi

PUBLIC_BASE="https://${DOMAIN}"

echo "3/4 Smoke HTTPS (${PUBLIC_BASE})"
python3 test_beta_smoke.py \
  --base "${PUBLIC_BASE}" \
  --admin-user "${ADMIN_USER}" \
  --admin-password "${ADMIN_PASSWORD}"

RELEASE=(python3 release_check.py --env .env --base "${PUBLIC_BASE}" --admin-user "${ADMIN_USER}" --admin-password "${ADMIN_PASSWORD}")
if [[ "${CHECK_CODEX_LIVE}" == "true" ]]; then
  RELEASE+=(--check-codex-live)
fi
if [[ "${PUBLIC_BETA}" == "true" ]]; then
  RELEASE+=(--public-beta)
fi

echo "4/4 Release gate"
"${RELEASE[@]}"

echo "Verificación VPS completada para ${PUBLIC_BASE}."
