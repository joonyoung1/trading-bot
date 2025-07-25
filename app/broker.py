import hashlib
import uuid as uuid_lib
from typing import Literal
from urllib.parse import urljoin, urlencode, unquote

import aiohttp
import jwt

from app.schemas.schemas import FGIResponse

from .schemas import Balance, Order, FGI
from config import Env
from .utils import retry


class Broker:
    def __init__(self):
        self.ACCESS = Env.ACCESS
        self.SECRET = Env.SECRET
        self.upbit_url = "https://api.upbit.com"
        self.datalab_url = "https://datalab-api.upbit.com"

    def initialize(self):
        self.session = aiohttp.ClientSession()

    async def request(
        self, method: Literal["GET", "POST", "DELETE"], url: str, **kwargs
    ):
        async with self.session.request(method=method, url=url, **kwargs) as response:
            return await response.json()

    @retry()
    async def get_current_price(self, ticker: str) -> float:
        params = {"markets": ticker}
        url = urljoin(self.upbit_url, "/v1/ticker")

        response = await self.request("GET", url, params=params)
        return response[0]["trade_price"]

    @retry()
    async def get_balances(self) -> dict[str, Balance]:
        headers = {"Authorization": self.generate_authorization()}
        url = urljoin(self.upbit_url, "/v1/accounts")

        response = await self.request("GET", url, headers=headers)
        balances = [Balance.model_validate(item) for item in response]
        return {balance.currency: balance for balance in balances}

    @retry()
    async def get_order(self, uuid: str) -> Order:
        params = {"uuid": uuid}
        headers = {"Authorization": self.generate_authorization(params=params)}
        url = urljoin(self.upbit_url, "/v1/order")

        response = await self.request("GET", url, params=params, headers=headers)
        return Order.model_validate(response)

    @retry()
    async def get_orders(self, uuids: list[str]) -> dict[str, Order]:
        params = {"uuids[]": uuids}
        headers = {"Authorization": self.generate_authorization(params=params)}
        url = urljoin(self.upbit_url, "/v1/orders/uuids")

        response = await self.request("GET", url, params=params, headers=headers)
        orders = [Order.model_validate(item) for item in response]
        order_map = {order.uuid: order for order in orders}

        for uuid in uuids:
            if uuid not in order_map:
                raise ValueError(f"Missing order data for UUID: {uuid}\n{order_map}")
        return order_map

    @retry()
    async def buy_limit_order(self, ticker: str, price: float, volume: float) -> Order:
        return await self.place_order(
            ticker, "bid", "limit", price=price, volume=volume
        )

    @retry()
    async def sell_limit_order(self, ticker: str, price: float, volume: float) -> Order:
        return await self.place_order(
            ticker, "ask", "limit", price=price, volume=volume
        )

    @retry()
    async def buy_market_order(self, ticker: str, price: float) -> Order:
        return await self.place_order(ticker, "bid", "price", price=price)

    @retry()
    async def sell_market_order(self, ticker: str, volume: float) -> Order:
        return await self.place_order(ticker, "ask", "market", volume=volume)

    @retry()
    async def place_order(
        self,
        ticker: str,
        side: Literal["bid", "ask"],
        ord_type: Literal["limit", "price", "market"],
        price: float | None = None,
        volume: float | None = None,
    ) -> Order:
        params: dict[str, str | float] = {
            "market": ticker,
            "side": side,
            "ord_type": ord_type,
        }
        if price:
            params["price"] = price
        if volume:
            params["volume"] = volume

        headers = {"Authorization": self.generate_authorization(params=params)}
        url = urljoin(self.upbit_url, "/v1/orders")

        response = await self.request("POST", url, json=params, headers=headers)
        return Order.model_validate(response)

    @retry()
    async def cancel_order(self, uuid: str) -> None:
        params = {"uuid": uuid}
        headers = {"Authorization": self.generate_authorization(params=params)}
        url = urljoin(self.upbit_url, "/v1/order")
        return await self.request("DELETE", url, params=params, headers=headers)

    @retry()
    async def cancel_orders(self, ticker: str) -> None:
        params = {"pairs": ticker}
        headers = {"Authorization": self.generate_authorization(params=params)}
        url = urljoin(self.upbit_url, "/v1/orders/open")
        return await self.request("DELETE", url, params=params, headers=headers)

    @retry()
    async def get_fgi(self, currency: str) -> FGI:
        pair = f"{currency}/KRW"
        url = urljoin(self.datalab_url, "api/v1/indicator/fear/assets")

        response = await self.request("GET", url, params={"locale": "ko"})
        records = response["data"]["records"]

        for record in records:
            record = FGIResponse.model_validate(record)
            if record.pair == pair:
                return FGI.from_response(record)

        raise ValueError(f"FGI data for currency {currency} not found")

    async def close(self):
        await self.session.close()

    @staticmethod
    def params_to_query_hash(params: dict):
        query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")
        m = hashlib.sha512()
        m.update(query_string)
        return m.hexdigest()

    def generate_authorization(self, params: dict | None = None):
        payload = {"access_key": self.ACCESS, "nonce": str(uuid_lib.uuid4())}
        if params:
            payload["query_hash"] = self.params_to_query_hash(params)
            payload["query_hash_alg"] = "SHA512"

        return f"Bearer {jwt.encode(payload, self.SECRET)}"
