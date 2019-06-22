from boilerpipe import Extractor, EXTRACTORS
from swisstext.cmd.scraping.tools import BsCrawler
from swisstext.cmd.scraping.interfaces import ICrawler
import click


class BpCrawler(ICrawler):

    def __init__(self, extractor=EXTRACTORS[0], min_words=5):
        if not extractor in EXTRACTORS:
            raise Exception(f'{extractor} is not a valid boilerpipe extractor class')

        self.extractor = Extractor(extractor, kMin=min_words)

    def crawl(self, url: str) -> ICrawler.CrawlResults:
        soup = BsCrawler.get_soup(url)
        sentences = self.extractor.getTextBlocks(html=str(soup))
        text = '\n'.join(sentences)

        return ICrawler.CrawlResults(text=text, links=BsCrawler.extract_links(url, soup))


@click.command()
@click.option('-e', '--extractor', type=click.Choice(EXTRACTORS), default=EXTRACTORS[0])
@click.option('-u', '--url', required=True, type=str)
@click.option('-n', '--min_words', default=5)
def cli(url, extractor, min_words):
    results = BpCrawler(extractor, min_words).crawl(url)
    print('===== TEXT =====')
    print(results.text)
    print('===== LINK =====')
    print('\n'.join(results.links))

@click.command()
@click.option('-e', '--extractor', type=click.Choice(EXTRACTORS), default=EXTRACTORS[0])
@click.option('-u', '--url', required=True, type=str)
@click.option('-n', '--min_words', default=5)
def test(url, extractor, min_words):
    # highly strange:
    # urls from stackoverflow fail
    # fails
    results1 = BpCrawler(extractor, min_words).crawl(url)
    results2 = BsCrawler().crawl(url)
    assert results1.links == results2.links, '\n'.join(set(results1.links) ^ set(results2.links))

if __name__ == "__main__":
    cli()
