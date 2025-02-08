import os
import jwt
import hashlib
import uuid
from typing import Literal

import aiohttp
from urllib.parse import urljoin, urlencode, unquote

from schemas import ConfigKeys


class Broker:
    def __init__(self):
        self.ACCESS = os.getenv(ConfigKeys.ACCESS)
        self.SECRET = os.getenv(ConfigKeys.SECRET)

        self.base_url = "https://api.upbit.com"
        self.session = aiohttp.ClientSession()

    async def request(
        self, method: Literal["GET", "POST", "DELETE"], url: str, **kwargs
    ):
        async with self.session.request(method=method, url=url, **kwargs) as response:
            return await response.json()

    async def get_current_price(self, ticker: str) -> float:
        params = {"markets": ticker}
        url = urljoin(self.base_url, "/v1/ticker")
        response = await self.request("GET", url, params=params)
        return response[0]["trade_price"]

    async def get_order(self, uuid: str):
        params = {"uuid": uuid}
        headers = {"Authorization": self.generate_authorization(params=params)}
        url = urljoin(self.base_url, "/v1/order")
        return await self.request("GET", url, params=params, headers=headers)

    async def get_orders(self, uuids: list[str]):
        params = {"uuids[]": uuids}
        headers = {"Authorization": self.generate_authorization(params=params)}
        url = urljoin(self.base_url, "/v1/orders/uuids")
        return await self.request("GET", url, params=params, headers=headers)

    async def get_balances(self):
        headers = {"Authorization": self.generate_authorization()}
        url = urljoin(self.base_url, "/v1/accounts")
        return await self.request("GET", url, headers=headers)

    async def buy_limit_order(self, ticker: str, price: float, volume: float):
        return await self.place_order(
            ticker, "bid", "limit", price=price, volume=volume
        )

    async def sell_limit_order(self, ticker: str, price: float, volume: float):
        return await self.place_order(
            ticker, "ask", "limit", price=price, volume=volume
        )

    async def buy_market_order(self, ticker: str, price: float):
        return await self.place_order(ticker, "bid", "price", price=price)

    async def sell_market_order(self, ticker: str, volume: float):
        return await self.place_order(ticker, "ask", "market", volume=volume)

    async def place_order(
        self,
        ticker: str,
        side: Literal["bid", "ask"],
        ord_type: Literal["limit", "price", "market"],
        price: float | None = None,
        volume: float | None = None,
    ):
        params = {"market": ticker, "side": side, "ord_type": ord_type}
        if price:
            params["price"] = price
        if volume:
            params["volume"] = volume

        headers = {"Authorization": self.generate_authorization(params=params)}
        url = urljoin(self.base_url, "/v1/orders")
        return await self.request("POST", url, json=params, headers=headers)

    async def cancel_orders(self, ticker: str):
        params = {"pairs": ticker}
        headers = {"Authorization": self.generate_authorization(params=params)}
        url = urljoin(self.base_url, "/v1/orders/open")
        return await self.request("DELETE", url, params=params, headers=headers)

    async def close(self):
        await self.session.close()

    @staticmethod
    def params_to_query_hash(params: dict):
        query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")
        m = hashlib.sha512()
        m.update(query_string)
        return m.hexdigest()

    def generate_authorization(self, params: dict | None = None):
        payload = {"access_key": self.ACCESS, "nonce": str(uuid.uuid4())}
        if params:
            payload["query_hash"] = self.params_to_query_hash(params)
            payload["query_hash_alg"] = "SHA512"

        return f"Bearer {jwt.encode(payload, self.SECRET)}"


if __name__ == "__main__":
    import asyncio

    async def main():
        broker = Broker()
        ticker = os.getenv(ConfigKeys.TICKER)

        # res = await broker.get_current_price(ticker)
        # res = await broker.get_balances()
        # res = await broker.cancel_orders(ticker)
        # res = await broker.place_order(ticker, "bid", "limit", price=1000, volume=5)
        # res = await broker.place_order(ticker, "ask", "limit", price=4000, volume=5)
        # res = await broker.sell_market_order(ticker, 2)
        # res = await broker.get_orders(["9dcd793e-fe23-4dcd-b3d3-e59fed220206"])
        res = await broker.get_order("9dcd793e-fe23-4dcd-b3d3-e59fed220206")
        print(res)

        await broker.close()

    asyncio.run(main())
