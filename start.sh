#!/bin/sh
set -eu

# Keep the PO-token server private to this container. The bgutil v2 server
# binds to localhost by default; we make that explicit.
node /opt/bgutil/server/build/main.js --host 127.0.0.1 --port 4416 &
POT_PID=$!

sleep 2
if ! kill -0 "$POT_PID" 2>/dev/null; then
  echo "ERROR: bgutil PO-token provider failed to start" >&2
  exit 1
fi

echo "INFO: bgutil PO-token provider running on 127.0.0.1:4416"

cleanup() {
  kill "$POT_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
