from src.crawler import Crawler
from rank_bm25 import BM25Okapi
import time


def main():
    start = "https://de.wikipedia.org/wiki/Grok"
    crawler = Crawler(start)

    start_time = time.perf_counter()
    pages_dict = crawler.multi_thread_crawl()
    end_time = time.perf_counter()

    elapsed_time = end_time - start_time
    print(f"The function took {elapsed_time:.4f} seconds")

    pages = [page for page in pages_dict.values()]
    splitted_texts = [page["text"].lower().split() for page in pages]

    bm25 = BM25Okapi(splitted_texts)
    while True:
        query = input()
        splitted_query = query.lower().split()
        top_pages = bm25.get_top_n(splitted_query, pages, n=5)
        print([page["url"] for page in top_pages])


if __name__ == "__main__":
    main()
