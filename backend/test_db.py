import asyncio
import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from models import Transaction

async def test():
    engine = create_async_engine('sqlite+aiosqlite:///./fraudguard.db')
    SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
    async with SessionLocal() as db:
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
        q = select(Transaction.created_at, Transaction.prediction).where(Transaction.created_at >= cutoff)
        result = await db.execute(q)
        rows = result.all()
        print('Rows count:', len(rows))
        if rows:
            print('First row type:', type(rows[0][0]))
            print('First row:', rows[0][0])

asyncio.run(test())
