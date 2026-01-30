#!/bin/bash
set -e

echo "Setting up virtual environment..."
python3 -m venv .venv --system-site-packages
"$(pwd)/.venv/bin/pip" install --upgrade pip
echo "Installing requirements..."
"$(pwd)/.venv/bin/pip" install -r requirements.txt
echo "cv2 installation skipped, make sure you have it installed globally"

SERVICE_NAME="jetson-car-autostart"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Paths
PROJECT_PATH="$(pwd)"
PYTHON_PATH="${PROJECT_PATH}/.venv/bin/python"
PYTHON_SCREEN_PATH="${PROJECT_PATH}/tools/screen.py"
PYTHON_MAIN_PATH="${PROJECT_PATH}/main.py"

echo "Downloading latest mediamtx release..."

cd ${PROJECT_PATH}/dashboard


if [ -f "./mediamtx" ]; then
    EXISTING_VERSION=$(./mediamtx --version 2>/dev/null || echo "unknown")
    echo "mediamtx already present: $EXISTING_VERSION"
    echo "Skipping download"
else
    curl -s https://api.github.com/repos/bluenviron/mediamtx/releases/latest | \
    grep "browser_download_url.*linux_arm64\.tar\.gz" | cut -d '"' -f 4 | \
    xargs curl -LO && \
    tar -xzf mediamtx_*_linux_arm64.tar.gz && \
    rm mediamtx_*_linux_arm64.tar.gz
cat > ./mediamtx.yml << 'EOF'
paths:
  live:
    source: publisher
EOF
fi

cd ${PROJECT_PATH}
echo "Done: mediamtx version = $(./dashboard/mediamtx --version)"

echo "Creating systemd service for $SERVICE_NAME"

cat <<EOF | sudo tee $SERVICE_FILE >/dev/null
[Unit]
Description=Autostart service for jetson-car

[Service]
Type=forking
TimeoutStartSec=0
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
