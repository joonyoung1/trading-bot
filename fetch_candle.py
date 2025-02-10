import asyncio
import pandas as pd
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

from app.broker import Broker


class CandleFetcher(Broker):
    async def get_candles(self, to: str) -> list[dict]:
        params = {"market": "KRW-XRP", "count": 144, "to": to}
        headers = {"Accept": "application/json"}
        url = urljoin(self.base_url, "/v1/candles/minutes/1")
        return await self.request("GET", url, params=params, headers=headers)


if __name__ == "__main__":
    now = datetime.now(timezone.utc)

    async def main():
        try:
            fetcher = CandleFetcher()
            fetcher.initialize()

            tos = [
                (now - timedelta(minutes=144 * x)).strftime("%Y-%m-%d %H:%M:%S")
                for x in range(70)
            ]

            tasks = [fetcher.get_candles(to=to) for to in tos]

            results = await asyncio.gather(*tasks)

            data = []
            for res in results[::-1]:
                for candle in res[::-1]:
                    # print(candle["candle_date_time_kst"])
                    data.append(
                        {
                            "timestamp": candle["candle_date_time_utc"],
                            "o": candle["opening_price"],
                            "h": candle["high_price"],
                            "l": candle["low_price"],
                            "t": candle["trade_price"],
                        }
                    )

            return pd.DataFrame(data)
        finally:
            await fetcher.close()

    data = asyncio.run(main())
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    data.to_csv("xrp_24h.csv", index=False)
