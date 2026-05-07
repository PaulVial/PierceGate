import asyncio
import os
from pathlib import Path

import asyncpg


async def run() -> None:
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    migrations_dir = Path(__file__).parent
    for sql_file in sorted(migrations_dir.glob("*.sql")):
        print(f"  → {sql_file.name}")
        await conn.execute(sql_file.read_text())
    await conn.close()
    print("Migrations complete.")


if __name__ == "__main__":
    asyncio.run(run())
