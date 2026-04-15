#!/bin/bash
set -euo pipefail

REPO_DIR="/home/ec2-user/ff-draft-room"
DIST_DIR="/var/www/ff-draft-room/dist"
NGINX_CONF="/etc/nginx/sites-available/ff-draft-room"
NGINX_ENABLED="/etc/nginx/sites-enabled/ff-draft-room"
SERVICE_FILE="/etc/systemd/system/ff-draft-room.service"

echo "==> Pulling latest code"
cd "$REPO_DIR"
git pull origin main

echo "==> Installing Python dependencies"
.venv/bin/pip install -r requirements.txt --quiet

echo "==> Building frontend"
cd frontend
npm ci --silent
# Vite reads frontend/.env.production automatically during build
npm run build
cd ..

echo "==> Copying frontend build"
sudo mkdir -p "$DIST_DIR"
sudo rsync -a --delete frontend/dist/ "$DIST_DIR/"

echo "==> Installing systemd service (first deploy only)"
if [ ! -f "$SERVICE_FILE" ]; then
    sudo cp scripts/ff-draft-room.service "$SERVICE_FILE"
    sudo systemctl daemon-reload
    sudo systemctl enable ff-draft-room
fi

echo "==> Installing nginx config (first deploy only)"
if [ ! -f "$NGINX_CONF" ]; then
    sudo cp scripts/nginx.conf.template "$NGINX_CONF"
    sudo ln -sf "$NGINX_CONF" "$NGINX_ENABLED"
    sudo nginx -t && sudo systemctl reload nginx
fi

echo "==> Restarting backend"
sudo systemctl restart ff-draft-room

echo "==> Waiting for backend to start"
sleep 3
curl -sf http://127.0.0.1:8000/health && echo " Backend healthy" \
    || echo "WARNING: health check failed"

echo "==> Deploy complete"
