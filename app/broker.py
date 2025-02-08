import os
import jwt
import hashlib
import uuid
from typing import Literal

import aiohttp
from urllib.parse import urljoin, urlencode, unquote

from schemas import ConfigKeys, Balance, Order


class Broker:
    def __init__(self):
        self.ACCESS = os.getenv(ConfigKeys.ACCESS)
        self.SECRET = os.getenv(ConfigKeys.SECRET)
        self.base_url = "https://api.upbit.com"
    
    def initialize(self):
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

    async def get_balances(self) -> dict[str, Balance]:
        headers = {"Authorization": self.generate_authorization()}
        url = urljoin(self.base_url, "/v1/accounts")

        response = await self.request("GET", url, headers=headers)
        balances = [Balance.model_validate(item) for item in response]
        return {
            (
                balance.currency
                if balance.currency == "KRW"
                else f"{balance.unit_currency}-{balance.currency}"
            ): balance
            for balance in balances
        }

    async def get_order(self, uuid: str) -> Order:
        params = {"uuid": uuid}
        headers = {"Authorization": self.generate_authorization(params=params)}
        url = urljoin(self.base_url, "/v1/order")

        response = await self.request("GET", url, params=params, headers=headers)
        return Order.model_validate(response)

    async def get_orders(self, uuids: list[str]) -> dict[str, Order]:
        params = {"uuids[]": uuids}
        headers = {"Authorization": self.generate_authorization(params=params)}
        url = urljoin(self.base_url, "/v1/orders/uuids")

        response = await self.request("GET", url, params=params, headers=headers)
        orders = [Order.model_validate(item) for item in response]
        return {order.uuid: order for order in orders}

    async def buy_limit_order(self, ticker: str, price: float, volume: float) -> Order:
        return await self.place_order(
            ticker, "bid", "limit", price=price, volume=volume
        )

    async def sell_limit_order(self, ticker: str, price: float, volume: float) -> Order:
        return await self.place_order(
            ticker, "ask", "limit", price=price, volume=volume
        )

    async def buy_market_order(self, ticker: str, price: float) -> Order:
        return await self.place_order(ticker, "bid", "price", price=price)

    async def sell_market_order(self, ticker: str, volume: float) -> Order:
        return await self.place_order(ticker, "ask", "market", volume=volume)

    async def place_order(
        self,
        ticker: str,
        side: Literal["bid", "ask"],
        ord_type: Literal["limit", "price", "market"],
        price: float | None = None,
        volume: float | None = None,
    ) -> Order:
        params = {"market": ticker, "side": side, "ord_type": ord_type}
        if price:
            params["price"] = price
        if volume:
            params["volume"] = volume

        headers = {"Authorization": self.generate_authorization(params=params)}
        url = urljoin(self.base_url, "/v1/orders")

        response = await self.request("POST", url, json=params, headers=headers)
        return Order.model_validate(response)
    
    async def cancel_order(self, uuid: str) -> None:
        params = {"uuid": uuid}
        headers = {"Authorization": self.generate_authorization(params=params)}
        url = urljoin(self.base_url, "/v1/order")
        return await self.request("DELETE", url, params=params, headers=headers)

    async def cancel_orders(self, ticker: str) -> None:
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
        try:
            broker = Broker()
            ticker = os.getenv(ConfigKeys.TICKER)

            # res = await broker.get_current_price(ticker)
            res = await broker.get_balances()
            # res = await broker.cancel_orders(ticker)
            # res = await broker.place_order(ticker, "bid", "limit", price=1000, volume=5)
            # res = await broker.place_order(ticker, "ask", "limit", price=4000, volume=5)
            # res = await broker.sell_market_order(ticker, 2)
            # res = await broker.get_orders(["4ae80662-461b-4cc6-af98-210bb619d579"])
            # res = await broker.get_order("4ae80662-461b-4cc6-af98-210bb619d579")
            print(res)
        finally:
            await broker.close()

    asyncio.run(main())
