#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/primer-empleado-ia}"
APP_USER="${APP_USER:-primeria}"
APP_GROUP="${APP_GROUP:-${APP_USER}}"
TARGET_DIR="${TARGET_DIR:-/etc/systemd/system}"

if [[ ! -f "deploy/primer-empleado-ia.service" || ! -f "deploy/primer-empleado-ia-backup.service" || ! -f "deploy/primer-empleado-ia-backup.timer" ]]; then
  echo "Ejecuta este script desde la raíz del repo, donde exista la carpeta deploy." >&2
  exit 1
fi

sed_escape() {
  printf '%s' "$1" | sed 's/[\/&]/\\&/g'
}

APP_DIR_ESCAPED="$(sed_escape "${APP_DIR}")"
APP_USER_ESCAPED="$(sed_escape "${APP_USER}")"
APP_GROUP_ESCAPED="$(sed_escape "${APP_GROUP}")"

mkdir -p "${TARGET_DIR}"

sed \
  -e "s/\/opt\/primer-empleado-ia/${APP_DIR_ESCAPED}/g" \
  -e "s/User=primeria/User=${APP_USER_ESCAPED}/g" \
  -e "s/Group=primeria/Group=${APP_GROUP_ESCAPED}/g" \
  deploy/primer-empleado-ia.service > "${TARGET_DIR}/primer-empleado-ia.service"

sed \
  -e "s/\/opt\/primer-empleado-ia/${APP_DIR_ESCAPED}/g" \
  -e "s/User=primeria/User=${APP_USER_ESCAPED}/g" \
  -e "s/Group=primeria/Group=${APP_GROUP_ESCAPED}/g" \
  deploy/primer-empleado-ia-backup.service > "${TARGET_DIR}/primer-empleado-ia-backup.service"

cp deploy/primer-empleado-ia-backup.timer "${TARGET_DIR}/primer-empleado-ia-backup.timer"
