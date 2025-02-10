import asyncio
from datetime import datetime, timezone, timedelta

from app.broker import Broker

async def fetch_price_series():
    now = datetime.now(timezone.utc)

    try:
        fetcher = Broker()
        fetcher.initialize()

        tos = [
            (now - timedelta(minutes=144 * x)).strftime("%Y-%m-%d %H:%M:%S")
            for x in range(70)
        ]

        tasks = [fetcher.get_candles(to, 144, "minute", 1) for to in tos]

        results = await asyncio.gather(*tasks)

        price_series = [results[-1][-1].opening_price]
        for candles in results[::-1]:
            for candle in candles[::-1]:
                if candle.opening_price < candle.trade_price:
                    price_series.extend(
                        [candle.low_price, candle.high_price, candle.trade_price]
                    )
                else:
                    price_series.extend(
                        [candle.high_price, candle.low_price, candle.trade_price]
                    )

        return price_series
    finally:
        await fetcher.close()
