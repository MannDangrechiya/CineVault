import asyncio
import asyncpg
import os
from services.api.config import config

async def check():
    host = os.getenv("POSTGRES_HOST") or "localhost"
    port = int(os.getenv("POSTGRES_PORT") or 5432)
    print(f"Connecting to {host}:{port}")
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=config.postgres_user,
            password=config.postgres_password,
            database=config.postgres_db
        )
        count = await conn.fetchval("SELECT count(*) FROM canonical.title;")
        print(f"Total titles: {count}")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(check())
