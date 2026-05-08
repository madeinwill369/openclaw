import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import AsyncOpenAI
from memory import init_db, save_memory, get_memories, save_message, get_recent_messages

# ── startup ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="OpenClaw", version="0.1.0", lifespan=lifespan)

openai_client = AsyncOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "sk-placeholder"),
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are OpenClaw, a personal AI agent running privately on the user's own server.
You remember facts about the user across conversations and use them to give personalised, helpful responses.
Be warm, direct, and concise. When the user tells you something worth remembering (preferences, facts about their life, goals), acknowledge it naturally — it's already being saved.
Never mention that you are built on ChatGPT or OpenAI. You are OpenClaw."""

# ── models ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"

class MemoryRequest(BaseModel):
    fact: str

# ── routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "app": "openclaw", "version": "0.1.0"}


@app.post("/chat")
async def chat(req: ChatRequest):
    memories = await get_memories(req.user_id)
    recent = await get_recent_messages(req.user_id, limit=10)

    memory_block = ""
    if memories:
        memory_block = "Facts you know about this user:\n" + "\n".join(f"- {m}" for m in memories) + "\n\n"

    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n" + memory_block}]
    for msg in recent:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": req.message})

    await save_message(req.user_id, "user", req.message)

    completion = await openai_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )
    response_text = completion.choices[0].message.content

    await save_message(req.user_id, "assistant", response_text)

    # auto-extract memories: if user states a fact about themselves, save it
    memory_triggers = ["my name is", "i am", "i'm", "i have", "i work", "i live", "i prefer", "i like", "i hate", "i don't like", "remember that", "remember i"]
    lower_msg = req.message.lower()
    if any(t in lower_msg for t in memory_triggers):
        await save_memory(req.user_id, req.message)

    all_memories = await get_memories(req.user_id)
    return {"response": response_text, "memory_count": len(all_memories)}


@app.get("/memory/{user_id}")
async def list_memories(user_id: str):
    memories = await get_memories(user_id)
    return {"user_id": user_id, "memories": memories, "count": len(memories)}


@app.post("/memory/{user_id}")
async def add_memory(user_id: str, req: MemoryRequest):
    await save_memory(user_id, req.fact)
    return {"saved": True, "fact": req.fact}


@app.get("/", response_class=HTMLResponse)
async def chat_ui():
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>OpenClaw</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0d0d0d;
      --surface: #1a1a1a;
      --border: #2a2a2a;
      --accent: #ff6b35;
      --text: #f0f0f0;
      --muted: #888;
      --user-bubble: #ff6b35;
      --agent-bubble: #1e1e1e;
    }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    header {
      width: 100%;
      max-width: 720px;
      padding: 20px 24px 12px;
      display: flex;
      align-items: center;
      gap: 12px;
      border-bottom: 1px solid var(--border);
    }
    .logo { font-size: 24px; }
    .brand { font-size: 18px; font-weight: 700; letter-spacing: -0.5px; }
    .brand span { color: var(--accent); }
    .badge {
      margin-left: auto;
      font-size: 11px;
      color: var(--muted);
      background: var(--surface);
      border: 1px solid var(--border);
      padding: 3px 8px;
      border-radius: 99px;
    }
    #chat-window {
      flex: 1;
      width: 100%;
      max-width: 720px;
      overflow-y: auto;
      padding: 24px 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .bubble-row {
      display: flex;
      align-items: flex-end;
      gap: 10px;
    }
    .bubble-row.user { flex-direction: row-reverse; }
    .bubble {
      max-width: 78%;
      padding: 12px 16px;
      border-radius: 18px;
      line-height: 1.55;
      font-size: 15px;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .bubble.user {
      background: var(--user-bubble);
      color: #fff;
      border-bottom-right-radius: 4px;
    }
    .bubble.agent {
      background: var(--agent-bubble);
      border: 1px solid var(--border);
      color: var(--text);
      border-bottom-left-radius: 4px;
    }
    .avatar {
      width: 30px; height: 30px;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 14px;
      flex-shrink: 0;
    }
    .avatar.agent { background: var(--accent); }
    .avatar.user { background: #333; }
    .thinking {
      display: flex; gap: 5px; padding: 14px 16px;
      background: var(--agent-bubble);
      border: 1px solid var(--border);
      border-radius: 18px;
      border-bottom-left-radius: 4px;
    }
    .dot {
      width: 7px; height: 7px;
      background: var(--muted);
      border-radius: 50%;
      animation: bounce 1.2s infinite ease-in-out;
    }
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes bounce {
      0%, 80%, 100% { transform: translateY(0); }
      40% { transform: translateY(-6px); }
    }
    #input-area {
      width: 100%;
      max-width: 720px;
      padding: 12px 16px 24px;
      display: flex;
      gap: 10px;
      border-top: 1px solid var(--border);
    }
    #msg-input {
      flex: 1;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      color: var(--text);
      padding: 12px 16px;
      font-size: 15px;
      resize: none;
      outline: none;
      line-height: 1.4;
      max-height: 140px;
      transition: border-color 0.15s;
    }
    #msg-input:focus { border-color: var(--accent); }
    #msg-input::placeholder { color: var(--muted); }
    #send-btn {
      background: var(--accent);
      border: none;
      border-radius: 12px;
      width: 48px;
      height: 48px;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
      transition: opacity 0.15s;
    }
    #send-btn:hover { opacity: 0.85; }
    #send-btn svg { width: 20px; height: 20px; fill: white; }
    .memory-pill {
      font-size: 11px;
      color: var(--muted);
      text-align: center;
      padding: 4px 0;
    }
  </style>
</head>
<body>
  <header>
    <div class="logo">🦀</div>
    <div class="brand">Open<span>Claw</span></div>
    <div class="badge" id="mem-badge">0 memories</div>
  </header>
  <div id="chat-window">
    <div class="bubble-row">
      <div class="avatar agent">🦀</div>
      <div class="bubble agent">Hey! I'm OpenClaw — your private AI agent running on your own server. Tell me anything about yourself and I'll remember it. What's on your mind?</div>
    </div>
  </div>
  <div id="input-area">
    <textarea id="msg-input" rows="1" placeholder="Message OpenClaw…"></textarea>
    <button id="send-btn">
      <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
    </button>
  </div>

  <script>
    const chatWindow = document.getElementById('chat-window');
    const input = document.getElementById('msg-input');
    const sendBtn = document.getElementById('send-btn');
    const memBadge = document.getElementById('mem-badge');
    const USER_ID = 'default';

    function addBubble(role, text) {
      const row = document.createElement('div');
      row.className = 'bubble-row ' + role;
      const av = document.createElement('div');
      av.className = 'avatar ' + role;
      av.textContent = role === 'agent' ? '🦀' : '🧑';
      const bub = document.createElement('div');
      bub.className = 'bubble ' + role;
      bub.textContent = text;
      row.appendChild(av);
      row.appendChild(bub);
      chatWindow.appendChild(row);
      chatWindow.scrollTop = chatWindow.scrollHeight;
      return row;
    }

    function showThinking() {
      const row = document.createElement('div');
      row.className = 'bubble-row';
      row.id = 'thinking';
      const av = document.createElement('div');
      av.className = 'avatar agent';
      av.textContent = '🦀';
      const bub = document.createElement('div');
      bub.className = 'thinking';
      bub.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
      row.appendChild(av);
      row.appendChild(bub);
      chatWindow.appendChild(row);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function removeThinking() {
      const el = document.getElementById('thinking');
      if (el) el.remove();
    }

    async function send() {
      const text = input.value.trim();
      if (!text) return;
      input.value = '';
      input.style.height = 'auto';
      addBubble('user', text);
      showThinking();
      sendBtn.disabled = true;
      try {
        const res = await fetch('/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: text, user_id: USER_ID})
        });
        const data = await res.json();
        removeThinking();
        addBubble('agent', data.response);
        memBadge.textContent = data.memory_count + ' memor' + (data.memory_count === 1 ? 'y' : 'ies');
      } catch(e) {
        removeThinking();
        addBubble('agent', 'Something went wrong. Make sure OpenClaw is configured correctly.');
      }
      sendBtn.disabled = false;
      input.focus();
    }

    sendBtn.addEventListener('click', send);
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
    });
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 140) + 'px';
    });

    // load memory count on start
    fetch('/memory/' + USER_ID).then(r => r.json()).then(d => {
      memBadge.textContent = d.count + ' memor' + (d.count === 1 ? 'y' : 'ies');
    }).catch(() => {});
  </script>
</body>
</html>""")
