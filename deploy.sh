#!/bin/bash

set -e

BOT_DIR="/opt/CBC_tg_bot"
SERVICE="cbc-bot"

echo "==> Pulling latest changes..."
cd "$BOT_DIR"
git pull

echo "==> Installing dependencies..."
poetry install --no-root

echo "==> Restarting service..."
systemctl restart "$SERVICE"

echo "==> Status:"
systemctl status "$SERVICE" --no-pager

echo ""
echo "==> Logs (Ctrl+C to exit):"
journalctl -u "$SERVICE" -f