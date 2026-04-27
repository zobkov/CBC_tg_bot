#!/bin/bash

set -e

BOT_DIR="/opt/CBC_tg_bot"
SERVICE="cbc_bot"

echo "==> Pulling latest changes..."
git -C "$BOT_DIR" pull

echo "==> Restarting service..."
systemctl restart "$SERVICE"

echo "==> Status:"
systemctl status "$SERVICE" --no-pager

echo ""
echo "==> Logs (Ctrl+C to exit):"
journalctl -u "$SERVICE" -f