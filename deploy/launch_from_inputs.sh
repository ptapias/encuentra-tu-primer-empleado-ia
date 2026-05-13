#!/usr/bin/env bash
set -euo pipefail

INPUTS_PATH="${INPUTS_PATH:-VPS_INPUTS.local.md}"
DOMAIN="${DOMAIN:-}"
APP_DIR="${APP_DIR:-/opt/primer-empleado-ia}"
APP_USER="${APP_USER:-primeria}"
APP_GROUP="${APP_GROUP:-${APP_USER}}"
CHECK_CODEX_LIVE="${CHECK_CODEX_LIVE:-true}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Ejecuta con sudo desde la raíz del repo en el VPS." >&2
  exit 1
fi

if [[ ! -f "app_server.py" || ! -d "deploy" ]]; then
  echo "Ejecuta desde la raíz del repo clonado." >&2
  exit 1
fi

if [[ ! -f "${INPUTS_PATH}" ]]; then
  echo "Falta ${INPUTS_PATH}. Crea una copia local: cp VPS_INPUTS.md VPS_INPUTS.local.md" >&2
  exit 2
fi

echo "1/6 Valido inputs de VPS"
python3 validate_vps_inputs.py --path "${INPUTS_PATH}"

echo "2/6 Genero .env.generated y privacy_config.json"
python3 prepare_vps_launch_files.py --inputs "${INPUTS_PATH}"

echo "3/6 Renderizo privacidad pública"
python3 render_privacy.py --config privacy_config.json

echo "4/6 Instalo aplicación y servicios"
APP_DIR="${APP_DIR}" \
APP_USER="${APP_USER}" \
APP_GROUP="${APP_GROUP}" \
DOMAIN="${DOMAIN}" \
CHECK_CODEX_LIVE="${CHECK_CODEX_LIVE}" \
./deploy/install_vps.sh

echo "5/6 Estado de preparación"
python3 beta_readiness_status.py || true

echo "6/6 Siguiente verificación"
if [[ -n "${DOMAIN}" ]]; then
  echo "Ejecuta ahora: DOMAIN=${DOMAIN} ./deploy/verify_vps.sh"
else
  echo "Instalación local completada. Define DOMAIN=tu-dominio para verificar HTTPS."
fi
