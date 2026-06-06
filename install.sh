#!/bin/bash
# ================================================================
# ocserv Web Manager - Installation Script
# ================================================================
set -e

INSTALL_DIR="/opt/ocserv-manager"
BACKEND_DIR="$INSTALL_DIR/backend"
FRONTEND_DIR="$INSTALL_DIR/frontend"
SERVICE_FILE="$INSTALL_DIR/ocserv-manager.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "=============================================="
echo "  ocserv Web Manager - Installation"
echo "=============================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root"
    exit 1
fi

# Check prerequisites
echo "[1/6] Checking prerequisites..."
for cmd in python3 node npm ocpasswd occtl; do
    if ! command -v $cmd &>/dev/null; then
        echo "  -> Installing missing: $cmd"
        case $cmd in
            python3) apt-get install -y python3 python3-pip python3-venv ;;
            node|npm) apt-get install -y nodejs npm ;;
            ocpasswd|occtl) echo "WARNING: $cmd not found, ocserv may not be installed" ;;
        esac
    fi
done
echo "  -> All prerequisites satisfied"

# Create virtual environment and install Python deps
echo "[2/6] Setting up Python backend..."
python3 -m venv "$BACKEND_DIR/venv"
source "$BACKEND_DIR/venv/bin/activate"
pip install --upgrade pip 2>/dev/null
pip install -r "$BACKEND_DIR/requirements.txt"
echo "  -> Backend dependencies installed"

# Build frontend
echo "[3/6] Building Vue3 frontend..."
cd "$FRONTEND_DIR"
if [ ! -d node_modules ]; then
    npm install --silent
fi
npm run build --silent
echo "  -> Frontend built: $FRONTEND_DIR/dist"

# Install systemd service
echo "[4/6] Installing systemd service..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/ocserv-manager.service"
systemctl daemon-reload
echo "  -> Service installed"

# Start service
echo "[5/6] Starting service..."
systemctl enable ocserv-manager
systemctl restart ocserv-manager
sleep 2

# Verify
echo "[6/6] Verifying..."
if systemctl is-active --quiet ocserv-manager; then
    echo "  -> Service is RUNNING"
else
    echo "  -> Service status: $(systemctl is-active ocserv-manager)"
    echo "  -> Check logs: journalctl -u ocserv-manager -n 20"
fi

echo ""
echo "=============================================="
echo "  Installation Complete!"
echo "=============================================="
echo ""
echo "  Web UI:  http://$(hostname -I | awk '{print $1}'):5000"
echo "  API:     http://$(hostname -I | awk '{print $1}'):5000/api"
echo ""
echo "  Service: systemctl {start|stop|restart|status} ocserv-manager"
echo "  Logs:    journalctl -u ocserv-manager -f"
echo ""
echo "  Default login: use your ocserv account credentials"
echo "  Admin user: 'admin' (or any user in 'admin' group)"
echo ""
