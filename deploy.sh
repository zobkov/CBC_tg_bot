#!/bin/bash

set -e

BOT_DIR="/opt/CBC_tg_bot"
SERVICE="cbc-bot"

echo "==> Pulling latest changes..."
sudo -u cbc_bot git -C "$BOT_DIR" pull

echo "==> Installing dependencies..."
sudo -u cbc_bot HOME="$BOT_DIR" bash -c "cd $BOT_DIR && poetry install --no-root"

echo "==> Restarting service..."
systemctl restart "$SERVICE"

echo "==> Status:"
systemctl status "$SERVICE" --no-pager

echo ""
echo "==> Logs (Ctrl+C to exit):"
journalctl -u "$SERVICE" -f