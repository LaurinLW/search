import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import time
from robotexclusionrulesparser import RobotExclusionRulesParser
import threading
import re
import html as html_lib
from requests.exceptions import HTTPError, ConnectionError
from datetime import datetime

HEADERS = {
    "User-Agent": "MyLittleSearchEngine/1.0 (mailto:laurin.leon.w@gmail.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


class Crawler:
    def __init__(self, start_url, max_pages=10000, delay=0.5):
        self.start_url = start_url
        self.max_pages = max_pages
        self.delay = delay

        self.forbitten = set()
        self.to_visit = {self.extract_host(self.start_url): set({self.start_url})}
        self.visited = set()

        self.lock = threading.Lock()

        self.pages = {}

        self.rp = RobotExclusionRulesParser()

    def extract_host(self, url):
        match = re.search(r"//(.*?)/", url)
        if match:
            extracted = match.group(1)
            return extracted
        return None

    def normalize_url(self, url):
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def is_allowed(self, url):
        allowed = True
        match = re.search(r"//(.*?)/", url)
        if match:
            extracted = match.group(1)
            with self.lock:
                allowed = not extracted in self.forbitten
        return self.rp.is_allowed("*", url) and allowed

    def extract_links(self, html, base_url):
        html = html_lib.unescape(html)
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)
            normalized = self.normalize_url(full_url)
            links.add(normalized)
        return links, soup

    def multi_thread_crawl(self):
        i = 0
        threads = []
        while (self.to_visit and len(self.visited) < self.max_pages) or len(threads):
            with self.lock:
                if self.to_visit and len(self.visited) + len(threads) < self.max_pages and len(threads) < 64:
                    url = ""
                    extracted_url = ""

                    running_urls = []
                    for ex_url, _ in threads:
                        running_urls.append(ex_url)
                    for entry in self.to_visit:
                        if not (entry in running_urls):
                            url = self.to_visit[entry].pop()
                            extracted_url = entry
                            if not self.to_visit[entry]:
                                self.to_visit.pop(entry)
                            break

                    if url:
                        thread = threading.Thread(target=self.crawl, args=(url,))
                        threads.append((extracted_url, thread))
                        thread.start()
                        i = i + 1
                        if i % 50 == 0:
                            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Visited {len(self.visited)}/{self.max_pages}, self.to_visit len is: {len(self.to_visit)}")
            alive_threads = []
            for url, thread in threads:
                if thread.is_alive():
                    alive_threads.append((url, thread))
                threads = alive_threads
        print(f"Finished with {len(self.pages)}")
        return self.pages

    def crawl(self, url):
        with self.lock:
            if url in self.visited:
                return

        if not self.is_allowed(url):
            print(f"Forbitten to access robots.txt: {url}")
            with self.lock:
                self.visited.add(url)
            return

        try:
            # print(f"Crawle: {url}")
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()

            if not response.headers["Content-Type"].startswith("text/html"):
                with self.lock:
                    self.visited.add(url)
                return

            html = response.text
            links, soup = self.extract_links(html, url)

            with self.lock:
                self.pages[url] = {
                    "html": html,
                    "title": soup.title.string if soup.title else "",
                    "text": soup.get_text(separator=" ", strip=True),
                    "links": list(links),
                    "status_code": response.status_code,
                    "crawled_at": time.time(),
                    "url": url,
                }

                for link in links:
                    host = self.extract_host(link)
                    if link not in self.visited and host not in self.forbitten:
                        if host in self.to_visit:
                            self.to_visit[host].add(link)
                        else:
                            self.to_visit[host] = set({link})

                self.visited.add(url)
            time.sleep(self.delay)
        except ConnectionError as e:
            with self.lock:
                match = re.search(r"//(.*?)/", url)
                if match:
                    extracted = match.group(1)
                    self.forbitten.add(extracted)
                    self.to_visit.pop(extracted, None)
        except HTTPError as e:
            if response.status_code == 403:
                with self.lock:
                    match = re.search(r"//(.*?)/", url)
                    if match:
                        extracted = match.group(1)
                        self.forbitten.add(extracted)
                        self.to_visit.pop(extracted, None)
        except Exception as e:
            print(f"Error at {url}: {e}")
            with self.lock:
                self.visited.add(url)
