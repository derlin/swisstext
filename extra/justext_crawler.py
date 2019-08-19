#
# requirements:
#   pip install justext
#

import argparse
import logging

import justext
from swisstext.cmd.scraping.interfaces import ICrawler
from swisstext.cmd.scraping.tools import BsCrawler

from extra.norm_punc import normalize_text

logger = logging.getLogger(__name__)


class JustextCrawler(BsCrawler):

    def __init__(self, joiner='\n',
                 keep_bad=True,
                 stoplist=None,
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
        logger.debug(self)

    def crawl(self, url: str):
        soup, content = self.get_soup(url)
        # For links, use bs4 (easier)
        links = self.extract_links(url, soup)

        try:
            # justext uses the decode/replace strategy by default, so encoding errors shouldn't happen
            # see justext core.py:DEFAULT_ENC_ERRORS
            paragraphs = justext.justext(content, encoding=soup.original_encoding, **self.kwargs)
            text_blocks = (p.text.replace('\n', ' ') for p in paragraphs if self._paragraph_ok(p))
            return ICrawler.CrawlResults(
                text=self.joiner.join(text_blocks),
                links=links)
        except Exception as e:
            if 'Document is empty' in str(e):
                # might happen if the content is not HTML/has no tags
                raise ICrawler.CrawlError(name='JustextError', message=str(e))
            raise e

    def _paragraph_ok(self, p):
        # look at context-free and accept neargood as well
        # "good" class may be skipped because the cf class is "short" (titles)
        return self.keep_bad or 'good' in p.cf_class
        #return self.keep_bad or p.class_type != 'bad'

    def __str__(self):
        return f'Justext({vars(self)})'.replace("'", '')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url', nargs='+')
    parser.add_argument('-joiner', default='\n')
    parser.add_argument('-norm', default=False, action='store_true', help='Also normalize text')
    parser.add_argument('-good', default=False, action='store_true', help='Keep only good|neargood sentences.')
    args = parser.parse_args()

    jt = JustextCrawler(joiner=args.joiner, keep_bad=not args.good)

    for url in args.url:
        try:
            res = jt.crawl(url)
            print(f'==== {url}')
            if args.norm:
                print(normalize_text(res.text))
            else:
                print(res.text)
        except Exception as e:
            print(e)
            # raise e