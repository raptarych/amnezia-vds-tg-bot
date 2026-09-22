#!/usr/bin/env bash
#
# Deploy and register the Amnezia VPN Telegram bot on Ubuntu 24.
#
# This script:
#   1. Creates a virtual environment and installs the bot dependencies.
#   2. Registers the bot as a systemd service for automatic start on boot.
#   3. Ensures the secrets YAML file exists (created with placeholders on the
#      first run so an operator can fill it in).
#
# Prerequisites:
#   - Run as root (sudo).
#   - The HTTP API must already be deployed and reachable.

set -euo pipefail

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="amnezia-vds-bot"
INSTALL_DIR="/opt/${SERVICE_NAME}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
CONFIG_FILE="/etc/amnezia-vds/bot.yml"

echo "==> Installing system dependencies"
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip

echo "==> Copying application to ${INSTALL_DIR}"
rm -rf "${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"
cp -r "${BOT_DIR}/app" "${INSTALL_DIR}/app"
cp -r "${BOT_DIR}/client" "${INSTALL_DIR}/client"
cp "${BOT_DIR}/pyproject.toml" "${INSTALL_DIR}/pyproject.toml"

echo "==> Preparing virtual environment"
python3 -m venv "${INSTALL_DIR}/.venv"
"${INSTALL_DIR}/.venv/bin/pip" install --upgrade pip
"${INSTALL_DIR}/.venv/bin/pip" install "${INSTALL_DIR}"

echo "==> Ensuring secrets config file at ${CONFIG_FILE}"
mkdir -p "$(dirname "${CONFIG_FILE}")"
if [ ! -f "${CONFIG_FILE}" ]; then
  cp "${BOT_DIR}/config.example.yml" "${CONFIG_FILE}"
  echo "Created placeholder config at ${CONFIG_FILE}. Fill it in and restart."
fi

echo "==> Writing systemd unit ${SERVICE_FILE}"
cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Amnezia VPN Telegram Bot
After=network.target amnezia-vds-api.service

[Service]
Type=simple
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/.venv/bin/python -m app.main
Restart=always
RestartSec=3
Environment="BOT_CONFIG_PATH=${CONFIG_FILE}"

[Install]
WantedBy=multi-user.target
EOF

echo "==> Enabling and restarting service"
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

sleep 3
systemctl status "${SERVICE_NAME}" --no-pager || true
echo "Bot deployment complete."
