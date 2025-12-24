from src.crawler import Crawler
from whoosh.index import open_dir, create_in, exists_in
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC, DATETIME, STORED
from whoosh.analysis import StemmingAnalyzer
from whoosh.qparser import MultifieldParser
import time
import os
from datetime import datetime

stem_analyzer = StemmingAnalyzer()
schema = Schema(
    url=ID(stored=True, unique=True),
    title=TEXT(stored=True, analyzer=stem_analyzer),
    text=TEXT(stored=False, analyzer=stem_analyzer),
    html=STORED(),
    links=KEYWORD(stored=True, commas=True, lowercase=True),
    status_code=NUMERIC(int, stored=True),
    crawled_at=DATETIME(stored=True),
)


def main():
    start = "https://de.wikipedia.org/wiki/Grok"
    crawler = Crawler(start)

    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")

    if not exists_in("indexdir"):
        ix = create_in("indexdir", schema)
    else:
        ix = open_dir("indexdir")

    start_time = time.perf_counter()
    pages_dict = crawler.multi_thread_crawl()
    end_time = time.perf_counter()

    elapsed_time = end_time - start_time
    print(f"The function took {elapsed_time:.4f} seconds")

    pages = [page for page in pages_dict.values()]

    start_time = time.perf_counter()

    with ix.writer(procs=4, limitmb=512, multisegment=True) as writer:
        for page in pages:
            writer.add_document(
                url=page["url"],
                title=page["title"],
                text=page["text"],
                html=page["html"],
                links=",".join(page["links"]),
                status_code=page["status_code"],
                crawled_at=datetime.fromtimestamp(page["crawled_at"]),
            )

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"The function took {elapsed_time:.4f} seconds")

    mp = MultifieldParser(["title", "text"], ix.schema, fieldboosts={"title": 2.0})
    with ix.searcher() as searcher:
        print("Ready to query :)")
        while True:
            user_query = input()

            query = mp.parse(user_query)
            results = searcher.search(query, limit=5)

            print([page["url"] for page in results])


if __name__ == "__main__":
    main()
