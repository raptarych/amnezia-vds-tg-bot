#!/usr/bin/env bash
#
# Deploy and register the Amnezia VPN management HTTP API on Ubuntu 24.
#
# This script:
#   1. Creates a virtual environment and installs the API dependencies.
#   2. Starts the API with uvicorn as a systemd service for automatic
#      start on boot.
#   3. Waits for the API to become reachable from outside.
#
# Prerequisites:
#   - The management script /root/awg/manage_amneziawg.sh must exist.
#   - Run as root (sudo).
#
# Optional environment variables:
#   AMNEZIA_API_SECRET       Fixed secret (otherwise auto-generated).
#   AMNEZIA_API_PORT         Listen port (default 8123).
#   AMNEZIA_API_BIND         Bind address (default 0.0.0.0).

set -euo pipefail

API_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="amnezia-vds-api"
INSTALL_DIR="/opt/${SERVICE_NAME}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

PORT="${AMNEZIA_API_PORT:-8123}"
BIND="${AMNEZIA_API_BIND:-0.0.0.0}"
SECRET_FILE="/etc/amnezia-vds/api_secret"

echo "==> Installing system dependencies"
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip

echo "==> Copying application to ${INSTALL_DIR}"
rm -rf "${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"
cp -r "${API_DIR}/app" "${INSTALL_DIR}/app"
cp "${API_DIR}/pyproject.toml" "${INSTALL_DIR}/pyproject.toml"
cp "${API_DIR}/gen_openapi.py" "${INSTALL_DIR}/gen_openapi.py"

echo "==> Preparing virtual environment"
python3 -m venv "${INSTALL_DIR}/.venv"
"${INSTALL_DIR}/.venv/bin/pip" install --upgrade pip
"${INSTALL_DIR}/.venv/bin/pip" install "${INSTALL_DIR}"

echo "==> Ensuring API secret file"
mkdir -p "$(dirname "${SECRET_FILE}")"
if [ ! -f "${SECRET_FILE}" ]; then
  if [ -n "${AMNEZIA_API_SECRET:-}" ]; then
    printf '%s\n' "${AMNEZIA_API_SECRET}" > "${SECRET_FILE}"
  else
    openssl rand -hex 24 > "${SECRET_FILE}"
    echo "Generated new API secret in ${SECRET_FILE}"
  fi
  chmod 600 "${SECRET_FILE}"
fi

echo "==> Writing systemd unit ${SERVICE_FILE}"
cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Amnezia VPN Management HTTP API
After=network.target

[Service]
Type=simple
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/.venv/bin/uvicorn app.main:app --host ${BIND} --port ${PORT}
Restart=always
RestartSec=3
Environment="AMNEZIA_API_SECRET_FILE=${SECRET_FILE}"
Environment="AMNEZIA_API_MANAGE_SCRIPT=/root/awg/manage_amneziawg.sh"
Environment="AMNEZIA_API_AWG_DIR=/root/awg"

[Install]
WantedBy=multi-user.target
EOF

echo "==> Enabling and starting service"
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

echo "==> Waiting for API to become reachable"
HOST_IP="$(hostname -I | awk '{print $1}')"
URL="http://${HOST_IP}:${PORT}/health"
for i in $(seq 1 30); do
  if curl -fsS "${URL}" > /dev/null 2>&1; then
    echo "API is reachable at ${URL}"
    systemctl status "${SERVICE_NAME}" --no-pager || true
    exit 0
  fi
  sleep 1
done

echo "ERROR: API did not become reachable at ${URL}" >&2
journalctl -u "${SERVICE_NAME}" -n 40 --no-pager >&2 || true
exit 1
