#!/bin/bash
echo "🦞 OpenClaw Setup"
if [ ! -f .env ]; then cp .env.example .env; fi
if [ -z "$OPENAI_API_KEY" ]; then
  read -p "Enter your OpenAI API key: " key
  sed -i "s/sk-your-key-here/$key/" .env
fi
echo "Starting OpenClaw..."
docker compose up -d
echo "OpenClaw running at http://localhost:8080"
