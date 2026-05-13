#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8787}"
AI_PROVIDER="${AI_PROVIDER:-codex}"
ALLOW_AI_FALLBACK="${ALLOW_AI_FALLBACK:-false}"
BETA_NOINDEX="${BETA_NOINDEX:-true}"
REPLACE="${REPLACE:-false}"

if [[ ! -f "app_server.py" || ! -f "Agente_Real_CRM.html" ]]; then
  echo "Ejecuta este script desde la raíz del proyecto MVP_Encuentra_Tu_Primer_Empleado_IA." >&2
  exit 1
fi

existing_pids=""
if command -v lsof >/dev/null 2>&1; then
  existing_pids="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
fi

if [[ -n "${existing_pids}" ]]; then
  if [[ "${REPLACE}" == "true" ]]; then
    echo "Puerto ${PORT} ocupado por ${existing_pids}. Parando servidor local anterior..."
    kill ${existing_pids} 2>/dev/null || true
    sleep 1
  else
    echo "El puerto ${PORT} ya está ocupado por ${existing_pids}." >&2
    echo "Para sustituir el servidor anterior ejecuta: REPLACE=true ./run_local_beta.sh" >&2
    exit 2
  fi
fi

export HOST PORT AI_PROVIDER ALLOW_AI_FALLBACK BETA_NOINDEX

echo "Arrancando beta local..."
echo "Proveedor IA: ${AI_PROVIDER}"
echo "Agente: http://${HOST}:${PORT}/Agente_Real_CRM.html"
echo "CRM:    http://${HOST}:${PORT}/CRM_Dashboard.html"

python3 app_server.py &
server_pid=$!

cleanup() {
  kill "${server_pid}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 1
if command -v curl >/dev/null 2>&1; then
  echo "Health:"
  curl -fsS "http://${HOST}:${PORT}/healthz" || true
  echo
fi

wait "${server_pid}"
