import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, func, case
from models import Transaction

async def test():
    engine = create_async_engine('sqlite+aiosqlite:///./fraudguard.db')
    SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
    async with SessionLocal() as db:
        count_q = select(
            func.count(Transaction.id).label("total"),
            func.sum(
                case((Transaction.prediction == 1, 1), else_=0)
            ).label("fraud_count"),
        )
        agg_result = await db.execute(count_q)
        agg = agg_result.one()
        print('Total:', agg.total, 'Fraud:', agg.fraud_count)

asyncio.run(test())
