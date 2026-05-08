#!/bin/bash
set -e

echo ""
echo "🦀 Welcome to OpenClaw setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# check docker
if ! command -v docker &> /dev/null; then
  echo "❌ Docker not found. Install Docker Desktop from https://docker.com and re-run."
  exit 1
fi

if ! docker compose version &> /dev/null; then
  echo "❌ Docker Compose not found. Update Docker Desktop and re-run."
  exit 1
fi

# set up .env
if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "Enter your OpenAI API key (get one at https://platform.openai.com/api-keys):"
read -r OPENAI_API_KEY

if [ -z "$OPENAI_API_KEY" ]; then
  echo "⚠️  No key entered. You can add it manually to .env before starting."
else
  # replace or append
  if grep -q "^OPENAI_API_KEY=" .env; then
    sed -i.bak "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_API_KEY|" .env
    rm -f .env.bak
  else
    echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> .env
  fi
  echo "✅ API key saved to .env"
fi

echo ""
echo "Starting OpenClaw..."
docker compose up -d --build

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ OpenClaw is running!"
echo ""
echo "   Chat UI  →  http://localhost:8080"
echo "   API docs →  http://localhost:8080/docs"
echo ""
echo "To stop:     docker compose down"
echo "To view logs: docker compose logs -f agent"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
