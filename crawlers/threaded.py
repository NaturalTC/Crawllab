import time
import requests
from bs4 import BeautifulSoup
from collections import deque
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from pymongo import MongoClient


class ThreadedCrawler:
    def __init__(self, seed_url: str, max_pages: int = 50,
                 mongo_uri: str | None = None, db_name: str = "webCrawlerArchive"):
        self.seed_url = seed_url
        self.max_pages = max_pages
        self._mongo_uri = mongo_uri
        self._db_name = db_name

    def _make_state(self) -> dict:
        return {"queue": deque([self.seed_url]), "visited": set(), "pages": 0, "collection": None}

    def _connect_mongo(self, state: dict):
        if self._mongo_uri:
            client = MongoClient(self._mongo_uri)
            state["collection"] = client[self._db_name].webpages
            state["collection"].delete_many({})

    def _fetch(self, url: str) -> str:
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            return r.text
        except Exception:
            return ""

    def _parse(self, url: str, html: str, state: dict):
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title else ""
        body = soup.body.get_text(" ", strip=True)[:500] if soup.body else ""

        if state["collection"] is not None:
            state["collection"].insert_one({"url": url, "title": title, "content": body})

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") and href not in state["visited"]:
                state["queue"].append(href)

    def _fetch_and_parse(self, url: str, state: dict):
        html = self._fetch(url)
        if html:
            self._parse(url, html, state)

    def crawl_single(self) -> float:
        state = self._make_state()
        self._connect_mongo(state)
        start = time.time()
        while state["queue"] and state["pages"] < self.max_pages:
            url = state["queue"].popleft()
            state["visited"].add(url)
            html = self._fetch(url)
            if html:
                self._parse(url, html, state)
                state["pages"] += 1
        return time.time() - start

    def crawl_threaded(self, max_workers: int = 10) -> float:
        state = self._make_state()
        self._connect_mongo(state)
        start = time.time()
        futures = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for _ in range(min(len(state["queue"]), max_workers)):
                url = state["queue"].popleft()
                state["visited"].add(url)
                futures.append(executor.submit(self._fetch_and_parse, url, state))

            while futures and state["pages"] < self.max_pages:
                done, _ = wait(futures, return_when=FIRST_COMPLETED)
                for fut in done:
                    fut.result()
                    state["pages"] += 1
                    futures.remove(fut)
                    if state["queue"]:
                        nxt = state["queue"].popleft()
                        state["visited"].add(nxt)
                        futures.append(executor.submit(self._fetch_and_parse, nxt, state))
        return time.time() - start
