#!/bin/bash
# Spuštění Planner serveru
# Použití: ./start.sh [port]

PORT=${1:-8000}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$SCRIPT_DIR/.env" ]; then
  echo "Soubor .env nenalezen – kopíruji z .env.example..."
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  echo "Upravte .env a nastavte ADMIN_TOKEN a BANK_ACCOUNT."
  exit 1
fi

if [ ! -d "$SCRIPT_DIR/.venv" ]; then
  echo "Virtuální prostředí nenalezeno – instaluji závislosti..."
  python3 -m venv "$SCRIPT_DIR/.venv"
  "$SCRIPT_DIR/.venv/bin/pip" install -q -r "$SCRIPT_DIR/backend/requirements.txt"
fi

echo "Spouštím Planner na http://localhost:$PORT"
cd "$SCRIPT_DIR/backend" && "$SCRIPT_DIR/.venv/bin/uvicorn" main:app --host 0.0.0.0 --port "$PORT" --reload
