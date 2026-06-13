import asyncio
import time
import aiohttp
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urljoin


class AsyncCrawler:
    def __init__(self, seed_url: str, max_pages: int = 50):
        self.seed_url = seed_url
        self.max_pages = max_pages

    async def _fetch(self, session: aiohttp.ClientSession, url: str) -> str:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return await resp.text()
        except Exception:
            return ""

    async def _parse(self, url: str, html: str, queue: deque, visited: set):
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            if href.startswith("http") and href not in visited:
                queue.append(href)

    async def _worker(self, session: aiohttp.ClientSession, sem: asyncio.Semaphore,
                      queue: deque, visited: set, counter: list):
        while counter[0] < self.max_pages and queue:
            url = queue.popleft()
            visited.add(url)
            async with sem:
                html = await self._fetch(session, url)
            if html:
                await self._parse(url, html, queue, visited)
            counter[0] += 1

    async def _run(self, concurrency: int) -> float:
        queue = deque([self.seed_url])
        visited: set = set()
        counter = [0]
        start = time.time()
        sem = asyncio.Semaphore(concurrency)
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.create_task(self._worker(session, sem, queue, visited, counter))
                     for _ in range(concurrency)]
            await asyncio.gather(*tasks)
        return time.time() - start

    def crawl(self, concurrency: int = 10) -> float:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._run(concurrency))
        finally:
            loop.close()
