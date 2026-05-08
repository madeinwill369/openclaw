from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio, os, openai
from memory import get_pool, init_db, save_message, get_messages, get_memories, save_memory, get_stats
from datetime import datetime

app = FastAPI(title="OpenClaw Agent")
pool = None
API_KEY = os.getenv("API_KEY", "openclaw-default")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup():
    global pool
    pool = await get_pool()
    await init_db(pool)

def check_auth(x_api_key: Optional[str] = None):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.get("/health")
async def health():
    return {"status": "ok", "service": "openclaw", "ts": datetime.utcnow().isoformat()}

@app.get("/stats/{user_id}")
async def stats(user_id: str, x_api_key: Optional[str] = Header(None)):
    check_auth(x_api_key)
    return await get_stats(pool, user_id)

@app.post("/chat")
async def chat(req: ChatRequest, x_api_key: Optional[str] = Header(None)):
    check_auth(x_api_key)
    await save_message(pool, req.user_id, "user", req.message)
    history = await get_messages(pool, req.user_id, limit=10)
    memories = await get_memories(pool, req.user_id)
    mem_context = "\n".join([f"- {m['key']}: {m['value']}" for m in memories]) if memories else "No memories yet."
    messages = [{"role": "system", "content": f"You are a helpful personal AI assistant. User memories:\n{mem_context}"}]
    messages += [{"role": m["role"], "content": m["content"]} for m in history]
    try:
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        resp = await client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        reply = resp.choices[0].message.content
    except Exception as e:
        reply = f"(LLM error: {e})"
    await save_message(pool, req.user_id, "assistant", reply)
    return {"reply": reply, "user_id": req.user_id}

@app.get("/memory/{user_id}")
async def memory(user_id: str, x_api_key: Optional[str] = Header(None)):
    check_auth(x_api_key)
    return {"memories": await get_memories(pool, user_id), "messages": await get_messages(pool, user_id)}

@app.get("/", response_class=HTMLResponse)
async def ui():
    return """<!DOCTYPE html>
<html><head><title>OpenClaw</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d0d0d;color:#e0e0e0;font-family:system-ui,sans-serif;height:100vh;display:flex;flex-direction:column}
header{padding:16px 24px;border-bottom:1px solid #1a1a1a;display:flex;align-items:center;gap:8px}
header h1{font-size:1.2rem;font-weight:700;color:#a78bfa}
#messages{flex:1;overflow-y:auto;padding:24px;display:flex;flex-direction:column;gap:12px}
.msg{max-width:70%;padding:12px 16px;border-radius:12px;font-size:.9rem;line-height:1.5}
.user{align-self:flex-end;background:#a78bfa;color:#fff;border-bottom-right-radius:4px}
.assistant{align-self:flex-start;background:#1a1a1a;color:#e0e0e0;border-bottom-left-radius:4px}
footer{padding:16px;border-top:1px solid #1a1a1a;display:flex;gap:8px}
input{flex:1;background:#1a1a1a;border:1px solid #333;color:#fff;padding:12px 16px;border-radius:8px;font-size:.9rem;outline:none}
input:focus{border-color:#a78bfa}
button{background:#a78bfa;color:#fff;border:none;padding:12px 20px;border-radius:8px;cursor:pointer;font-weight:600}
button:hover{background:#9061f9}
</style></head>
<body>
<header><h1>🦞 OpenClaw</h1><span style="color:#666;font-size:.8rem">personal AI agent</span></header>
<div id="messages"></div>
<footer>
<input id="inp" placeholder="Message your agent..." onkeydown="if(event.key==='Enter')send()">
<button onclick="send()">Send</button>
</footer>
<script>
const uid='user-'+Math.random().toString(36).slice(2,8);
const msgs=document.getElementById('messages');
function addMsg(role,text){
  const d=document.createElement('div');
  d.className='msg '+role;d.textContent=text;msgs.appendChild(d);
  msgs.scrollTop=msgs.scrollHeight;
}
async function send(){
  const inp=document.getElementById('inp');
  const msg=inp.value.trim();if(!msg)return;
  inp.value='';addMsg('user',msg);
  const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json','X-API-Key':'openclaw-default'},body:JSON.stringify({user_id:uid,message:msg})});
  const d=await r.json();addMsg('assistant',d.reply);
}
addMsg('assistant','Hello! I am your personal OpenClaw agent. How can I help?');
</script>
</body></html>"""
