#!/usr/bin/env bash
# Sobe API (porta 5000) e front (porta 5500). Ctrl+C encerra os dois.
cd "$(dirname "$0")" || exit 1
PY="$(pwd)/backend/.venv/bin/python"

if [ ! -x "$PY" ]; then
  echo "Ambiente virtual nao encontrado. Faca uma vez:"
  echo "  cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

[ -f backend/.env ] || cp backend/.env.example backend/.env

if [ ! -f backend/instance/sabor_clic.db ]; then
  echo "Criando o banco de dados pela primeira vez..."
  (cd backend && "$PY" -m flask --app run init-db --sim)
fi

(cd backend && exec "$PY" run.py) &
API=$!
(cd frontend && exec "$PY" -m http.server 5500 --bind 127.0.0.1) &
FRONT=$!
trap 'kill "$API" "$FRONT" 2>/dev/null' EXIT INT TERM

sleep 2
echo "Abra http://127.0.0.1:5500  (Ctrl+C para encerrar)"
command -v xdg-open >/dev/null 2>&1 && xdg-open http://127.0.0.1:5500 >/dev/null 2>&1 &
wait
