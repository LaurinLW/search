import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import time
from robotexclusionrulesparser import RobotExclusionRulesParser
from collections import deque

HEADERS = {
    "User-Agent": "MyLittleSearchEngine/1.0 (mailto:laurin.leon.w@gmail.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


class Crawler:
    def __init__(self, start_url, max_pages=100, delay=1.0):
        self.start_url = start_url
        self.max_pages = max_pages
        self.delay = delay

        parsed = urlparse(start_url)
        self.domain = parsed.netloc
        self.base_scheme = parsed.scheme

        self.to_visit = deque([start_url])
        self.visited = set()

        self.pages = {}

        self.rp = RobotExclusionRulesParser()

    def normalize_url(self, url):
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def is_allowed(self, url):
        return self.rp.is_allowed("*", url)

    def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)
            normalized = self.normalize_url(full_url)

            if urlparse(normalized).netloc == self.domain:
                links.add(normalized)
        return links, soup

    def crawl(self):
        print(f"Crawling from {self.start_url} (max {self.max_pages} pages)")

        while self.to_visit and len(self.visited) < self.max_pages:
            url = self.to_visit.popleft()

            if url in self.visited:
                continue

            if not self.is_allowed(url):
                print(f"Forbitten to access robots.txt: {url}")
                self.visited.add(url)
                continue

            try:
                print(f"[{len(self.visited)+1}/{self.max_pages}] Crawle: {url}")
                response = requests.get(url, headers=HEADERS, timeout=10)
                response.raise_for_status()

                if not response.headers["Content-Type"].startswith("text/html"):
                    self.visited.add(url)
                    continue

                html = response.text
                links, soup = self.extract_links(html, url)

                self.pages[url] = {"html": html, "title": soup.title.string if soup.title else "", "text": soup.get_text(separator=" ", strip=True), "links": list(links), "status_code": response.status_code, "crawled_at": time.time()}

                for link in links:
                    if link not in self.visited and link not in self.to_visit:
                        self.to_visit.append(link)

                self.visited.add(url)
                time.sleep(self.delay)

            except Exception as e:
                print(f"Error at {url}: {e}")
                self.visited.add(url)

        print(f"\nCrawled {len(self.pages)} pages.")
        return self.pages
