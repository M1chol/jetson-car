#!/bin/bash
set -e

echo "Setting up virtual environment..."
python3 -m venv .venv
"$(pwd)/.venv/bin/pip" install --upgrade pip
"$(pwd)/.venv/bin/pip" install -r requirements.txt

SERVICE_NAME="jetson-car-autostart"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Paths
PROJECT_PATH="$(pwd)"
PYTHON_PATH="${PROJECT_PATH}/.venv/bin/python"
PYTHON_SCREEN_PATH="${PROJECT_PATH}/tools/screen.py"
PYTHON_MAIN_PATH="${PROJECT_PATH}/main.py"

echo "Creating systemd service for $SERVICE_NAME"

cat <<EOF | sudo tee $SERVICE_FILE >/dev/null
[Unit]
Description=Autostart service for jetson-car

[Service]
Type=simple
ExecStart=${PYTHON_PATH} ${PYTHON_SCREEN_PATH} &
ExecStartPost=${PYTHON_PATH} ${PYTHON_MAIN_PATH}
Restart=on-failure
User=$(whoami)
WorkingDirectory=${PROJECT_PATH}
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service

echo "Installed ${SERVICE_NAME}.service"
