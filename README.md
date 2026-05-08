# OpenClaw 🦞

> Self-hostable personal AI agent. One command setup.

OpenClaw is an open-source personal AI agent you can run on your own infrastructure. It gives you a private chat interface, persistent memory, and a simple API — all running in Docker with no external dependencies except an OpenAI API key.

## Quick Start

```bash
git clone https://github.com/madeinwill369/openclaw
cd openclaw
./setup.sh
```

## What you get
- 💬 Private chat UI (dark theme, runs in browser)
- 🧠 Persistent memory per user (stored in Postgres)
- 🔌 REST API (POST /chat, GET /memory/{user_id})
- 🐳 Docker Compose — agent + database, one command
- 🔑 Simple API key auth

## Architecture
- FastAPI backend
- PostgreSQL for memory storage
- OpenAI GPT-4 for responses
- Self-hosted, your data stays yours

## Stack
- Python 3.11, FastAPI, asyncpg
- PostgreSQL 15
- Docker Compose

Built by SCANA.
