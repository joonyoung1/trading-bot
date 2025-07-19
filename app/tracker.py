from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy.future import select

from .models import SessionLocal, History


class Tracker:
    async def record_trade(self, value: float, price: float, ratio: float) -> None:
        async with SessionLocal() as session:
            history = History(
                timestamp=datetime.now(),
                balance=value,
                price=price,
                ratio=ratio,
            )
            session.add(history)
            await session.commit()

    async def get_recent_histories(self) -> pd.DataFrame:
        time_limit = datetime.now() - timedelta(days=90)

        async with SessionLocal() as session:
            query = (
                select(History)
                .where(History.timestamp >= time_limit)
                .order_by(History.timestamp.asc())
            )
            result = await session.execute(query)
            histories = result.scalars().all()

        data = [(h.timestamp, h.balance, h.price, h.ratio) for h in histories]

        return pd.DataFrame(
            data,
            columns=pd.Index(
                [
                    History.timestamp.name,
                    History.balance.name,
                    History.price.name,
                    History.ratio.name,
                ]
            ),
        )
