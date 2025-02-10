import asyncio
import pandas as pd
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

from app.broker import Broker


if __name__ == "__main__":
    now = datetime.now(timezone.utc)

    async def main():
        try:
            fetcher = Broker()
            fetcher.initialize()

            tos = [
                (now - timedelta(minutes=144 * x)).strftime("%Y-%m-%d %H:%M:%S")
                for x in range(70)
            ]

            tasks = [fetcher.get_candles(to, 144, "minute", 1) for to in tos]

            results = await asyncio.gather(*tasks)

            data = []
            for candles in results[::-1]:
                for candle in candles[::-1]:
                    data.append(
                        {
                            "timestamp": candle.candle_date_time_utc,
                            "o": candle.opening_price,
                            "h": candle.high_price,
                            "l": candle.low_price,
                            "t": candle.trade_price,
                        }
                    )

            return pd.DataFrame(data)
        finally:
            await fetcher.close()

    data = asyncio.run(main())
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    data.to_csv("xrp_24h.csv", index=False)
