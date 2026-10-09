#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "------------------------------------------------------------"
echo "[*] Stopping any existing agent containers..."
for compose_file in agents/*/docker/docker-compose.yml; do
    [ -f "$compose_file" ] || continue
    (cd "$(dirname "$compose_file")" && docker compose down)
done
echo "Existing agent containers stopped successfully."
if [ -d agents/skyvern/docker/.streamlit ]; then
    echo "! To clear previous agent's data, we require sudo privileges to remove the .streamlit directory."
    sudo rm -rf agents/skyvern/docker/.streamlit
    sudo rm -rf agents/skyvern/docker/postgres-data
fi
echo "------------------------------------------------------------"
echo

echo "------------------------------------------------------------"
echo "[*] Loading and validating .env"
if [ ! -f .env ]; then
    echo ".env file not found. Please create one before running this script."
    exit 1
fi

# Load .env into the current shell so we can validate values.
set -a
source .env
set +a

case "${ACTION:-}" in
    TERMINATE|CLICK|INPUT|PROMPT) ;;
    *) echo "Invalid ACTION='${ACTION:-}' in .env (must be TERMINATE, CLICK, INPUT, or PROMPT)."; exit 1 ;;
esac

case "${AGENT:-}" in
    YURA|AGENTE|SKYVERN) ;;
    *) echo "Invalid AGENT='${AGENT:-}' in .env (must be YURA, AGENTE, or SKYVERN)."; exit 1 ;;
esac

case "${MODE:-}" in
    ATTACK|DEFENSE) ;;
    *) echo "Invalid MODE='${MODE:-}' in .env (must be ATTACK or DEFENSE)."; exit 1 ;;
esac

case "${BREAKER_LLM:-}" in
    GPT|LLAMA) ;;
    *) echo "Invalid BREAKER_LLM='${BREAKER_LLM:-}' in .env (must be GPT or LLAMA)."; exit 1 ;;
esac

# Determine which API keys are required based on BREAKER_LLM
_need_openai=true; _need_llama=false
case "${BREAKER_LLM}" in
    GPT)   _need_openai=true ;;
    LLAMA) _need_llama=true ;;
esac

if $_need_openai && [ -z "${GPT_API_KEY:-}" ]; then echo "GPT_API_KEY is missing in .env (required for GPT).";  exit 1; fi
if $_need_llama  && [ -z "${LLAMA_API_KEY:-}" ];  then echo "LLAMA_API_KEY is missing in .env (required for LLAMA)."; exit 1; fi
echo ".env loaded and validated successfully."
echo "------------------------------------------------------------"
echo 


echo "------------------------------------------------------------"
echo "[*] Validating API keys"
if $_need_openai; then
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        https://api.openai.com/v1/chat/completions \
        -H "Authorization: Bearer ${GPT_API_KEY}" \
        -H "Content-Type: application/json" \
        -d '{"model":"gpt-4.1","messages":[{"role":"user","content":"hi"}],"max_tokens":1}')
    if [ "$HTTP_STATUS" != "200" ]; then
        echo "GPT_API_KEY validation failed (HTTP $HTTP_STATUS)."; exit 1
    fi
    echo "GPT_API_KEY is valid."
fi
if $_need_llama; then
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        https://api.novita.ai/openai/v1/chat/completions \
        -H "Authorization: Bearer ${LLAMA_API_KEY}" \
        -H "Content-Type: application/json" \
        -d '{"model":"meta-llama/llama-4-scout-17b-16e-instruct","messages":[{"role":"user","content":"hi"}],"max_tokens":1}')
    if [ "$HTTP_STATUS" != "200" ]; then
        echo "LLAMA_API_KEY validation failed (HTTP $HTTP_STATUS)."; exit 1
    fi
    echo "LLAMA_API_KEY is valid."
fi
echo "------------------------------------------------------------"
echo

echo "------------------------------------------------------------"
echo "[*] Current .env settings"
while IFS='=' read -r key value; do
    [ -z "$key" ] && continue
    case "$key" in
        \#*) continue ;;
        GPT_API_KEY|LLAMA_API_KEY|SECRET_FOR_LEAK_PROMPT) continue ;;
    esac
    printf "  %-10s: %s\n" "$key" "$value"
done < .env
echo

read -rp "Proceed with this .env? [y/N]: " CONFIRM
case "$CONFIRM" in
    y|Y) ;;
    *) echo "Aborted. Edit .env and re-run."; exit 1 ;;
esac
echo "------------------------------------------------------------"
echo 
echo "------------------------------------------------------------"
echo "[*] Generating agent docker-compose file"
docker run --rm \
    -v "$(pwd)/agents:/app/agents" \
    -v "$(pwd)/.env:/app/.env" \
    agentbreaker:latest python3 generate_agents_compose_file.py
echo

AGENT_LOWER=$(echo "$AGENT" | tr '[:upper:]' '[:lower:]')


echo "Starting ${AGENT} container"

cd "agents/${AGENT_LOWER}/docker" && docker compose up -d
sleep 10
echo "------------------------------------------------------------"
echo