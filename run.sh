#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://${OLLAMA_HOST}}"
MAIN_MODEL="${OLLAMA_MODEL:-deepseek-r1:1.5b}"
EXTRACTOR_MODEL="${OLLAMA_EXTRACTOR_MODEL:-qwen2.5:0.5b}"
LOCAL_LLM_MODEL="${LOCAL_LLM_MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"

BACKEND_PID=""
FRONTEND_PID=""
OLLAMA_PID=""
STARTED_OLLAMA="0"
OLLAMA_MODE="none" # cli | docker | none
DOCKER_OLLAMA_CONTAINER="llmo-ollama"
OLLAMA_AVAILABLE="0"
CLEANED_UP="0"

cleanup() {
  if [[ "${CLEANED_UP}" == "1" ]]; then
    return
  fi
  CLEANED_UP="1"
  echo ""
  echo "Stopping services..."
  if [[ -n "${FRONTEND_PID}" ]] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
  fi
  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
    kill "${BACKEND_PID}" 2>/dev/null || true
  fi
  if [[ "${STARTED_OLLAMA}" == "1" ]] && [[ "${OLLAMA_MODE}" == "cli" ]] && [[ -n "${OLLAMA_PID}" ]] && kill -0 "${OLLAMA_PID}" 2>/dev/null; then
    kill "${OLLAMA_PID}" 2>/dev/null || true
  fi
  if [[ "${STARTED_OLLAMA}" == "1" ]] && [[ "${OLLAMA_MODE}" == "docker" ]]; then
    docker rm -f "${DOCKER_OLLAMA_CONTAINER}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

wait_for_ollama() {
  local retries=40
  local delay=0.5
  for _ in $(seq 1 "${retries}"); do
    if curl -sSf "${OLLAMA_BASE_URL}/api/tags" >/dev/null 2>&1; then
      return 0
    fi
    sleep "${delay}"
  done
  return 1
}

wait_for_backend() {
  local retries=60
  local delay=0.5
  for _ in $(seq 1 "${retries}"); do
    if curl -sSf "http://127.0.0.1:${BACKEND_PORT}/api/schema/" >/dev/null 2>&1; then
      return 0
    fi
    # If backend process crashed, fail fast.
    if [[ -n "${BACKEND_PID}" ]] && ! kill -0 "${BACKEND_PID}" 2>/dev/null; then
      return 1
    fi
    sleep "${delay}"
  done
  return 1
}

if ! command -v npm >/dev/null 2>&1; then
  echo "Error: 'npm' not found in PATH."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: 'python3' not found in PATH."
  exit 1
fi

echo "Checking Ollama..."
if ! curl -sSf "${OLLAMA_BASE_URL}/api/tags" >/dev/null 2>&1; then
  if command -v ollama >/dev/null 2>&1; then
    echo "Ollama is not running. Starting ollama serve..."
    ollama serve >/tmp/llmo-ollama.log 2>&1 &
    OLLAMA_PID=$!
    STARTED_OLLAMA="1"
    OLLAMA_MODE="cli"
  elif command -v docker >/dev/null 2>&1; then
    echo "'ollama' CLI not found. Starting Ollama in Docker..."
    docker rm -f "${DOCKER_OLLAMA_CONTAINER}" >/dev/null 2>&1 || true
    docker run -d \
      --name "${DOCKER_OLLAMA_CONTAINER}" \
      -p 11434:11434 \
      -v ollama_data:/root/.ollama \
      ollama/ollama:latest >/dev/null
    STARTED_OLLAMA="1"
    OLLAMA_MODE="docker"
  else
    echo "Warning: Neither 'ollama' nor 'docker' found in PATH."
    echo "Backend/frontend will start without LLM (fallback mode)."
  fi
else
  OLLAMA_AVAILABLE="1"
fi

if [[ "${STARTED_OLLAMA}" == "1" ]]; then
  if ! wait_for_ollama; then
    echo "Warning: Ollama did not become ready at ${OLLAMA_BASE_URL}"
    echo "Continuing in fallback mode without LLM."
  else
    OLLAMA_AVAILABLE="1"
  fi
fi

if [[ "${OLLAMA_AVAILABLE}" == "1" ]]; then
  echo "Ensuring models are available..."
  if command -v ollama >/dev/null 2>&1; then
    ollama pull "${MAIN_MODEL}"
    ollama pull "${EXTRACTOR_MODEL}"
  elif [[ "${OLLAMA_MODE}" == "docker" ]]; then
    docker exec "${DOCKER_OLLAMA_CONTAINER}" ollama pull "${MAIN_MODEL}"
    docker exec "${DOCKER_OLLAMA_CONTAINER}" ollama pull "${EXTRACTOR_MODEL}"
  fi
fi

echo "Setting up Python environment..."
cd "${ROOT_DIR}"

if [[ "${START_INFRA:-0}" == "1" ]] && command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    echo "START_INFRA=1: starting Neo4j + Qdrant (docker compose)..."
    docker compose -f "${ROOT_DIR}/docker-compose.yml" up -d neo4j qdrant || echo "Warning: docker compose up failed (continuing)."
  else
    echo "Warning: START_INFRA=1 but 'docker compose' not available."
  fi
fi

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi
PIP_ARGS=()
if [[ "${PIP_QUIET:-1}" == "1" ]]; then
  PIP_ARGS+=(-q)
fi
.venv/bin/python -m pip install "${PIP_ARGS[@]}" -r requirements.txt

if [[ "${PRELOAD_LOCAL_MODEL:-1}" == "1" ]]; then
  echo "Preloading local model (${LOCAL_LLM_MODEL})..."
  LOCAL_LLM_MODEL="${LOCAL_LLM_MODEL}" .venv/bin/python -c "from src.local_llm import warmup_local_llm; warmup_local_llm()" || \
    echo "Warning: local model preload failed. It will retry on first chat request."
fi

echo "Starting backend on http://127.0.0.1:${BACKEND_PORT} ..."
.venv/bin/python manage.py runserver "0.0.0.0:${BACKEND_PORT}" &
BACKEND_PID=$!

echo "Waiting for backend to become ready..."
if ! wait_for_backend; then
  echo "Error: Backend did not become ready on port ${BACKEND_PORT}."
  exit 1
fi

echo "Starting frontend on http://127.0.0.1:${FRONTEND_PORT} ..."
cd "${ROOT_DIR}/frontend"
npm install
npm run dev -- --host 127.0.0.1 --port "${FRONTEND_PORT}" &
FRONTEND_PID=$!

echo ""
echo "Services are starting:"
if [[ "${OLLAMA_AVAILABLE}" == "1" ]]; then
  echo "- Ollama:   ${OLLAMA_BASE_URL}"
else
  echo "- Ollama:   unavailable (using local model ${LOCAL_LLM_MODEL})"
fi
echo "- Backend:  http://127.0.0.1:${BACKEND_PORT}"
echo "- Frontend: http://127.0.0.1:${FRONTEND_PORT}"
echo ""
echo "Press Ctrl+C to stop everything started by this script."

wait "${BACKEND_PID}" "${FRONTEND_PID}"
