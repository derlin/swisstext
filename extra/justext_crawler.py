#
# requirements:
#   pip install justext
#

import argparse
import logging

import justext
from bs4 import BeautifulSoup
from swisstext.cmd.scraping.interfaces import ICrawler
from swisstext.cmd.scraping.tools import BsCrawler

from extra.norm_punc import normalize_text

logger = logging.getLogger(__name__)


class JustextCrawler(BsCrawler):

    def __init__(self, joiner='\n',
                 keep_bad=True,
                 stoplist=None,
                 normalize=False,
                 stopwords_low=justext.core.STOPWORDS_LOW_DEFAULT,
                 stopwords_high=justext.core.STOPWORDS_HIGH_DEFAULT,
                 **kwargs):
        super().__init__(joiner=joiner)

        if stoplist is not None:
            with open(stoplist) as f:
                self.kwargs = dict(
                    stoplist=set(l.strip() for l in f if len(l)),
                    stopwords_low=stopwords_low,
                    stopwords_high=stopwords_high)
        else:
            self.kwargs = dict(stoplist=set(), stopwords_low=0, stopwords_high=0)

        self.kwargs.update(kwargs)
        self.keep_bad = keep_bad
        self.normalize = normalize
        logger.debug(self)

    def crawl(self, url: str):
        content = self.get_content(url)
        # get links using bs4 (easier)
        soup = BeautifulSoup(content, 'html.parser')
        links = self.extract_links(url, soup)
        # use raw content, as str(soup) is somewhat altered HTML and doesn't work as well...
        paragraphs = justext.justext(content, encoding=soup.original_encoding, **self.kwargs)
        text_blocks = (p.text.replace('\n', ' ') for p in paragraphs if self._paragraph_ok(p))
        if self.normalize:
            # TODO: maybe use the fix_encoding option as well (nice, but quite slow)
            text_blocks = [normalize_text(t) for t in text_blocks]
        return ICrawler.CrawlResults(
            text=self.joiner.join(text_blocks),
            links=links)

    def _paragraph_ok(self, p):
        return self.keep_bad or p.class_type != 'bad'

    def __str__(self):
        return f'Justext({vars(self)})'.replace("'", '')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url', nargs='+')
    parser.add_argument('-joiner', default='\n')
    parser.add_argument('-norm', default=False, action='store_true', help='Also normalize text')
    parser.add_argument('-good', default=False, action='store_true', help='Keep only good|neergood sentences.')
    args = parser.parse_args()

    jt = JustextCrawler(joiner=args.joiner, keep_bad=not args.good, normalize=args.norm)
    for url in args.url:
        try:
            res = jt.crawl(url)
            print(f'==== {url}')
            print(res.text)
        except Exception as e:
            print(e)
            # raise e
