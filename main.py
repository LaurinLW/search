from src.crawler import Crawler


def main():
    start = "https://de.wikipedia.org/wiki/Wikipedia:Hauptseite"
    crawler = Crawler(start)
    pages = crawler.crawl()


if __name__ == "__main__":
    main()
