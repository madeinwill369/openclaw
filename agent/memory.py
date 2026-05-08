import asyncpg, os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://openclaw:openclaw@db:5432/openclaw")

async def get_pool():
    return await asyncpg.create_pool(DATABASE_URL)

async def init_db(pool):
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS memories (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(user_id, key)
            );
        """)

async def save_message(pool, user_id: str, role: str, content: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO messages (user_id, role, content) VALUES ($1, $2, $3)",
            user_id, role, content
        )

async def get_messages(pool, user_id: str, limit: int = 20):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT role, content, created_at FROM messages WHERE user_id=$1 ORDER BY created_at DESC LIMIT $2",
            user_id, limit
        )
        return [dict(r) for r in reversed(rows)]

async def save_memory(pool, user_id: str, key: str, value: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO memories (user_id, key, value) VALUES ($1,$2,$3) ON CONFLICT (user_id,key) DO UPDATE SET value=EXCLUDED.value",
            user_id, key, value
        )

async def get_memories(pool, user_id: str):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT key, value, created_at FROM memories WHERE user_id=$1", user_id)
        return [dict(r) for r in rows]

async def get_stats(pool, user_id: str):
    async with pool.acquire() as conn:
        msg_count = await conn.fetchval("SELECT COUNT(*) FROM messages WHERE user_id=$1", user_id)
        mem_count = await conn.fetchval("SELECT COUNT(*) FROM memories WHERE user_id=$1", user_id)
        return {"messages": msg_count, "memories": mem_count}
