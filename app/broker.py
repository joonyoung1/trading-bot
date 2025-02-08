import os
import jwt
import hashlib
import uuid

import aiohttp
from urllib.parse import urljoin, urlencode, unquote

from schemas import ConfigKeys


class Broker:
    def __init__(self):
        self.ACCESS = os.getenv(ConfigKeys.ACCESS)
        self.SECRET = os.getenv(ConfigKeys.SECRET)

        self.base_url = "https://api.upbit.com"
        self.session = aiohttp.ClientSession()

    async def request(self, method: str, url: str, **kwargs) -> dict:
        async with self.session.request(method=method, url=url, **kwargs) as response:
            return await response.json()

    async def get_balances(self):
        payload = {
            "access_key": self.ACCESS,
            "nonce": str(uuid.uuid4()),
        }
        headers = {
            "Authorization": f"Bearer {jwt.encode(payload, self.SECRET)}",
        }

        url = urljoin(self.base_url, "/v1/accounts")
        return await self.request("GET", url, headers=headers)



    async def close(self):
        await self.session.close()


if __name__ == "__main__":
    import asyncio

    async def main():
        broker = Broker()

        res = await broker.get_balances()
        print(res)

        await broker.close()

    asyncio.run(main())
