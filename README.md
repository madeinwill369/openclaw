# 🦀 OpenClaw

**Your personal AI agent, self-hosted.**

OpenClaw gives you a private, persistent AI that remembers everything, connects to your apps, and runs on your own server. No subscriptions. No data leaving your infrastructure. One command setup.

---

## Why OpenClaw?

Most AI assistants are rented. You pay monthly, your conversations train their models, and the day you stop paying — it's gone. OpenClaw is yours. It runs on a $5 VPS, a Raspberry Pi, or your laptop. Your memory, your data, your agent.

---

## Quick Start

```bash
git clone https://github.com/madeinwill369/openclaw.git
cd openclaw
chmod +x setup.sh
./setup.sh
```

That's it. OpenClaw will be running at **http://localhost:8080** in under 2 minutes.

**Requirements:** Docker + Docker Compose (that's all)

---

## Features

- 💬 **Persistent memory** — OpenClaw remembers facts about you across every conversation
- 🔒 **Fully private** — nothing leaves your server, ever
- 🤖 **OpenAI-compatible** — works with OpenAI, Ollama, Mistral, Groq, or any compatible API
- 🌐 **Clean chat UI** — no setup required, open your browser and talk
- 🐘 **Postgres-backed** — production-grade storage, not a JSON file
- 🐳 **One-command deploy** — Docker Compose handles everything
- 🔌 **REST API** — integrate with anything via simple HTTP endpoints
- 📦 **Self-contained** — agent + database, no external dependencies

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Your Server                   │
│                                                 │
│   ┌──────────────────┐   ┌──────────────────┐  │
│   │   OpenClaw Agent  │   │   PostgreSQL DB  │  │
│   │   (FastAPI)       │◄──►   memories       │  │
│   │   port 8080       │   │   messages       │  │
│   └────────┬─────────┘   └──────────────────┘  │
│            │                                    │
└────────────┼────────────────────────────────────┘
             │ HTTPS
             ▼
    ┌─────────────────┐
    │  LLM Provider   │
    │  OpenAI / local │
    └─────────────────┘
             ▲
             │
    ┌─────────────────┐
    │   Your Browser  │
    │   chat UI       │
    └─────────────────┘
```

**Data flow:**
1. You send a message via the chat UI or API
2. Agent loads your recent messages + stored memories from Postgres
3. Builds a context-aware prompt and calls your LLM
4. Saves the exchange and any new memories back to Postgres
5. Returns the response instantly

---

## API Reference

### Chat
```
POST /chat
{"message": "Remember I prefer dark mode", "user_id": "you"}
→ {"response": "Got it!", "memory_count": 3}
```

### Memory
```
GET  /memory/{user_id}         → list all memories
POST /memory/{user_id}         → {"fact": "I have two dogs"}
```

### Health
```
GET /health → {"status": "ok", "app": "openclaw", "version": "0.1.0"}
```

---

## Configuration

Edit `.env` before starting:

```
OPENAI_API_KEY=your-key-here
```

To use a local model (Ollama, LM Studio, etc.), set:
```
OPENAI_BASE_URL=http://host.docker.internal:11434/v1
OPENAI_MODEL=llama3
```

---

## Roadmap

- [ ] Email integration (IMAP/SMTP)
- [ ] Telegram + iMessage connectors
- [ ] Web search tool
- [ ] Calendar awareness
- [ ] Multi-user support
- [ ] Plugin system
- [ ] One-click Railway / Render deploy

---

## License

MIT. Fork it, build on it, sell it. Just keep the spirit alive.

---

*OpenClaw is the open-source foundation of [folk](https://folk.ai) — the personal AI agent by Nozomio Labs.*
