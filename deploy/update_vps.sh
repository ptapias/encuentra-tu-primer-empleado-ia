#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/primer-empleado-ia}"
APP_USER="${APP_USER:-primeria}"
APP_GROUP="${APP_GROUP:-${APP_USER}}"
ADMIN_USER="${ADMIN_USER:-admin}"
DOMAIN="${DOMAIN:-}"
CHECK_CODEX_LIVE="${CHECK_CODEX_LIVE:-true}"
BROWSER_CHECKS="${BROWSER_CHECKS:-false}"
TRANSCRIPTION_CHECK="${TRANSCRIPTION_CHECK:-false}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Ejecuta este script con sudo desde el VPS." >&2
  exit 1
fi

if [[ ! -d "${APP_DIR}/.git" ]]; then
  echo "No encuentro un repo Git en ${APP_DIR}. Usa install_vps.sh para la primera instalación." >&2
  exit 1
fi

cd "${APP_DIR}"

if [[ ! -f ".env" ]]; then
  echo "Falta ${APP_DIR}/.env. No actualizo sin configuración." >&2
  exit 1
fi

env_value() {
  local key="$1"
  awk -F= -v key="${key}" '$1 == key { sub(/^[^=]*=/, ""); gsub(/^'\''|'\''$/, ""); gsub(/^"|"$/, ""); print; exit }' .env
}

ADMIN_PASSWORD="${ADMIN_PASSWORD:-$(env_value ADMIN_PASSWORD)}"
if [[ -z "${ADMIN_PASSWORD}" || "${ADMIN_PASSWORD}" == "change-me" ]]; then
  echo "ADMIN_PASSWORD no está configurada con un valor real." >&2
  exit 1
fi

GIT=(git -c safe.directory="${APP_DIR}")

privacy_dirty_files() {
  "${GIT[@]}" status --porcelain -- PRIVACY_BETA.md PRIVACY_BETA.html | awk '{print $2}'
}

only_generated_privacy_dirty() {
  local status all_files privacy_files
  status="$("${GIT[@]}" status --porcelain)"
  if [[ -z "${status}" ]]; then
    return 1
  fi

  all_files="$(printf '%s\n' "${status}" | awk '{print $2}' | sort)"
  privacy_files="$(privacy_dirty_files | sort)"

  [[ -n "${privacy_files}" && "${all_files}" == "${privacy_files}" && -f privacy_config.json ]]
}

restore_generated_privacy_before_pull() {
  if only_generated_privacy_dirty; then
    echo "Detecto privacidad renderizada localmente. La regenero después del pull desde privacy_config.json."
    "${GIT[@]}" checkout -- PRIVACY_BETA.md PRIVACY_BETA.html
    return 0
  fi

  if ! "${GIT[@]}" diff --quiet || ! "${GIT[@]}" diff --cached --quiet; then
    echo "El repo tiene cambios locales. No actualizo para no pisar trabajo manual en el VPS." >&2
    echo "Si solo has generado la privacidad final, conserva privacy_config.json y vuelve a lanzar el update." >&2
    exit 1
  fi
}

rerender_privacy_if_configured() {
  if [[ -f privacy_config.json ]]; then
    python3 render_privacy.py --config privacy_config.json
  fi
}

restore_generated_privacy_before_pull

BEFORE="$("${GIT[@]}" rev-parse --short HEAD)"
ROLLBACK_ENABLED=false

render_systemd_units() {
  if [[ -x ./deploy/render_systemd_units.sh ]]; then
    APP_DIR="${APP_DIR}" APP_USER="${APP_USER}" APP_GROUP="${APP_GROUP}" ./deploy/render_systemd_units.sh
  fi
}

rollback() {
  local exit_code=$?
  if [[ "${ROLLBACK_ENABLED}" == "true" ]]; then
    echo "Actualización fallida. Intento rollback a ${BEFORE}..." >&2
    "${GIT[@]}" reset --hard "${BEFORE}" || true
    rerender_privacy_if_configured || true
    chown -R "${APP_USER}:${APP_GROUP}" "${APP_DIR}" || true
    render_systemd_units || true
    systemctl daemon-reload || true
    systemctl restart primer-empleado-ia || true
  fi
  exit "${exit_code}"
}
trap rollback ERR

echo "1/8 Backup antes de actualizar"
python3 backup_crm.py || {
  echo "Backup falló. No actualizo." >&2
  exit 1
}

echo "2/8 Pull de GitHub desde ${BEFORE}"
"${GIT[@]}" fetch origin main
"${GIT[@]}" pull --ff-only origin main
AFTER="$("${GIT[@]}" rev-parse --short HEAD)"
if [[ "${AFTER}" != "${BEFORE}" ]]; then
  ROLLBACK_ENABLED=true
fi

rerender_privacy_if_configured

echo "3/8 Permisos"
chown -R "${APP_USER}:${APP_GROUP}" "${APP_DIR}"
chmod 700 "${APP_DIR}"
chmod 600 "${APP_DIR}/.env"

PREFLIGHT=(python3 preflight_vps.py --env .env --service-user "${APP_USER}")
if [[ "${CHECK_CODEX_LIVE}" == "true" ]]; then
  PREFLIGHT+=(--check-codex-live)
fi

echo "4/8 Preflight"
"${PREFLIGHT[@]}"

echo "5/8 Release check estático"
python3 release_check.py --env .env

echo "6/8 Actualizo unidades systemd"
render_systemd_units
systemctl daemon-reload

echo "7/8 Reinicio servicio"
systemctl restart primer-empleado-ia
sleep 2

HOST_VALUE="$(env_value HOST)"
PORT_VALUE="$(env_value PORT)"
PORT_VALUE="${PORT_VALUE:-8787}"
LOCAL_BASE="http://${HOST_VALUE:-127.0.0.1}:${PORT_VALUE}"

echo "8/8 Smoke local (${LOCAL_BASE})"
python3 test_beta_smoke.py \
  --base "${LOCAL_BASE}" \
  --admin-user "${ADMIN_USER}" \
  --admin-password "${ADMIN_PASSWORD}"

if [[ -n "${DOMAIN}" ]]; then
  echo "Verificación HTTPS con dominio ${DOMAIN}"
  DOMAIN="${DOMAIN}" \
  ADMIN_USER="${ADMIN_USER}" \
  ADMIN_PASSWORD="${ADMIN_PASSWORD}" \
  APP_USER="${APP_USER}" \
  CHECK_CODEX_LIVE="${CHECK_CODEX_LIVE}" \
  BROWSER_CHECKS="${BROWSER_CHECKS}" \
  TRANSCRIPTION_CHECK="${TRANSCRIPTION_CHECK}" \
  ./deploy/verify_vps.sh
fi

ROLLBACK_ENABLED=false
echo "Actualización completada: ${BEFORE} -> ${AFTER}"
