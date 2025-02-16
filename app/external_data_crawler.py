import os
import aiohttp

from bs4 import BeautifulSoup

from constants import ConfigKeys


class ExternalDataCrawler:
    def __init__(self):
        self.TICKER = os.getenv(ConfigKeys.TICKER)

    async def request(self):
        pass

    async def crawl_fgi(self):
        pass

    async def parse_fgi(self, soup: BeautifulSoup):
        pass