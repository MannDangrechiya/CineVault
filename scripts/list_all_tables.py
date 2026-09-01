import asyncio
import asyncpg
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.api.config import config

async def main():
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST") or "localhost",
        port=int(os.getenv("POSTGRES_PORT") or 5432),
        user=config.postgres_user,
        password=config.postgres_password,
        database=config.postgres_db
    )
    rows = await conn.fetch("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema') ORDER BY table_schema, table_name;")
    for r in rows:
        print(f"{r['table_schema']}.{r['table_name']}")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
