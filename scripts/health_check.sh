#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-6000}"
MAX_RETRIES=30
RETRY_INTERVAL=1

echo "[health_check] Starting Flask server in background on port ${PORT}..."
python app.py &
SERVER_PID=$!

cleanup() {
  echo "[health_check] Stopping server (PID=${SERVER_PID})..."
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

echo "[health_check] Waiting for server to become ready..."
for i in $(seq 1 "$MAX_RETRIES"); do
  if curl -sf "http://localhost:${PORT}/api/health" > /dev/null 2>&1; then
    echo "[health_check] Server is healthy (attempt ${i}/${MAX_RETRIES})."
    RESPONSE=$(curl -s "http://localhost:${PORT}/api/health")
    echo "[health_check] Response: ${RESPONSE}"
    exit 0
  fi
  sleep "$RETRY_INTERVAL"
done

echo "[health_check] ERROR: Server did not become healthy after ${MAX_RETRIES} retries." >&2
exit 1
